package main

import (
	"crypto/rand"
	"encoding/hex"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
	"time"
)

// Store is the in-memory container/exec registry plus the fakehost template
// reference. Concurrency-safe.
type Store struct {
	mu           sync.Mutex
	containers   map[string]*Container
	execs        map[string]*Exec
	templateRoot string
	workRoot     string
}

// Container models a shim-managed "container" — a staged rootfs with a
// declared Cmd and Binds that may or may not have been started yet.
type Container struct {
	ID      string
	Name    string
	Image   string
	Cmd     []string
	Env     []string
	Binds   []string
	Tty     bool
	WorkDir string

	Rootfs  string // per-container staged rootfs path on the sidecar
	Created time.Time
	Started time.Time
	Exited  time.Time

	State    string // "created", "running", "exited"
	ExitCode int

	Stdout []byte
	Stderr []byte

	// Internal execution coordination.
	done chan struct{}
	cmd  *exec.Cmd
}

// Exec models a /containers/{id}/exec instance.
type Exec struct {
	ID          string
	ContainerID string
	Cmd         []string
	Env         []string
	AttachOut   bool
	AttachErr   bool
	Tty         bool

	Stdout   []byte
	Stderr   []byte
	ExitCode int
	Running  bool
	done     chan struct{}
}

func NewStore(template, workdir string) *Store {
	return &Store{
		containers:   make(map[string]*Container),
		execs:        make(map[string]*Exec),
		templateRoot: template,
		workRoot:     workdir,
	}
}

// newID returns a 64-hex-character ID matching Docker's native format.
func newID() string {
	b := make([]byte, 32)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

// Add creates a new Container, stages a per-container rootfs from the
// template (cp -a), applies the bind-map by copying requested sources into
// their target paths within the rootfs, and returns it.
func (s *Store) Add(c *Container) error {
	c.ID = newID()
	c.Rootfs = filepath.Join(s.workRoot, c.ID, "rootfs")
	c.Created = time.Now().UTC()
	c.State = "created"
	c.done = make(chan struct{})

	if err := os.MkdirAll(c.Rootfs, 0755); err != nil {
		return err
	}

	// Copy template tree. Using cp -a preserves modes and symlinks; cheap
	// for our ~5MB template.
	cp := exec.Command("cp", "-a",
		s.templateRoot+"/.", c.Rootfs+"/")
	if out, err := cp.CombinedOutput(); err != nil {
		return wrapErr("stage rootfs", err, string(out))
	}

	// Apply binds. For each "src:dst[:ro]" entry, copy the source tree from
	// the sidecar's fakehost template (NOT from the sidecar's real root) into the
	// rootfs at dst. This is how the classic `-v /:/host` exploitation move
	// shows up: the competitor mounts "/" of the "host" and we populate
	// /host inside their rootfs with what appears to be the host's FS.
	for _, b := range c.Binds {
		if err := applyBind(s.templateRoot, c.Rootfs, b); err != nil {
			// Best-effort; don't fail the create. Real Docker validates
			// binds at create but tolerates a lot.
			logErr("bind %q: %v", b, err)
		}
	}

	s.mu.Lock()
	s.containers[c.ID] = c
	s.mu.Unlock()
	return nil
}

// Lookup finds a container by full ID or ID prefix (>=6 chars) or name.
func (s *Store) Lookup(idOrName string) *Container {
	s.mu.Lock()
	defer s.mu.Unlock()
	if c, ok := s.containers[idOrName]; ok {
		return c
	}
	if len(idOrName) >= 6 {
		for id, c := range s.containers {
			if len(id) >= len(idOrName) && id[:len(idOrName)] == idOrName {
				return c
			}
		}
	}
	for _, c := range s.containers {
		if c.Name == idOrName || c.Name == "/"+idOrName {
			return c
		}
	}
	return nil
}

// LookupExec finds an exec instance by ID.
func (s *Store) LookupExec(id string) *Exec {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.execs[id]
}

// List returns all known containers, optionally filtered to running only.
func (s *Store) List(all bool) []*Container {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := make([]*Container, 0, len(s.containers))
	for _, c := range s.containers {
		if !all && c.State != "running" {
			continue
		}
		out = append(out, c)
	}
	return out
}

// Remove tears down a container's rootfs and drops it from the registry.
// Supports full ID, short-ID prefix, or name — same as Lookup.
func (s *Store) Remove(idOrName string) bool {
	c := s.Lookup(idOrName)
	if c == nil {
		return false
	}
	s.mu.Lock()
	delete(s.containers, c.ID)
	s.mu.Unlock()
	if c.Rootfs != "" {
		_ = os.RemoveAll(filepath.Dir(c.Rootfs))
	}
	return true
}

func (s *Store) AddExec(e *Exec) {
	e.ID = newID()
	e.done = make(chan struct{})
	s.mu.Lock()
	s.execs[e.ID] = e
	s.mu.Unlock()
}

// Shutdown cleans up all per-container rootfs staging dirs on exit.
func (s *Store) Shutdown() {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, c := range s.containers {
		if c.Rootfs != "" {
			_ = os.RemoveAll(filepath.Dir(c.Rootfs))
		}
	}
}
