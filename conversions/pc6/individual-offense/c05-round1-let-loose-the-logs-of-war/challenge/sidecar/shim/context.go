package main

import "context"

type ctxKey int

const (
	ctxKeyPathParams ctxKey = iota
)

func withPathParams(ctx context.Context, params []string) context.Context {
	return context.WithValue(ctx, ctxKeyPathParams, params)
}

func pathParams(ctx context.Context) []string {
	if v, ok := ctx.Value(ctxKeyPathParams).([]string); ok {
		return v
	}
	return nil
}
