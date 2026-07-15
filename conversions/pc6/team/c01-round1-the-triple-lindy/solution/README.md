# The Triple Lindy

*Solution Guide*

## Overview

In *The Triple Lindy*, teams perform a penetration test against a local swimming pool. Players will use the provided Kali machine to gather data and exploit websites and SCADA/ICS systems to ensure the pool's safe operation.

There are four (4) tokens to retrieve in this challenge. All tokens will be available in the Townsville Pool website as they are unlocked by completing the steps below.

*The Triple Lindy* is an infinity-style challenge. The tokens you see in this solution guide will have different values but will use the same format.

For your convenience, we've repeated some of the challenge instructions here in the challenge solution guide.

Start by logging into the `kali` VM, then browse to `http://townsville-pool.pccc` to gather information about the Townsville Pool's technical operations. `ctmodbus` and `pymodbus` have been installed on the Kali VMs. A DNS server at `dns.pccc` resolves challenge hostnames — use `--dns-servers dns.pccc` with nmap scans.

## Question 1

*What is the value of token 1 that is awarded after logging into the Townsville Pool's website as the pool president?*

1. Open a web browser on your Kali VM and navigate to: `http://townsville-pool.pccc`.

![Firefox on the Kali VM showing the Townsville Community Pool home page, with a top navigation bar (Home, Facilities, Our Team, Live Cameras, Admin, etc.) above a hero image of poolside umbrellas and palm trees.](./img/c01-01.PNG "Townsville Pool website home page")

2. Click **Our Team**. Here you will find the email addresses of some of the pool staff, including the pool president.

![The pool website's Our Team page listing pool staff members with their names, titles, and email addresses.](./img/c01-02.PNG "Our Team page with staff email addresses")

![Detail of the Our Team listing highlighting the pool president's entry and email address (jamie.johns@townsvillepool.pccc).](./img/c01-03.PNG "Pool president's email address")

3. The next step is to find the president's password. In a new terminal, run `cewl` to create a list of possible passwords from the website's content:

```bash
cewl -v http://townsville-pool.pccc > passwords.txt
```

![Kali terminal running cewl against the pool website in verbose mode, scraping page content into a wordlist redirected to passwords.txt.](./img/c01-04.PNG "Generating a password wordlist with cewl")

Now that we have a potential list of passwords, we will try brute forcing the login. Examine the login form.

4. On the Townsville Community Pool website, click **Member Login**.

![The pool website's Member Login page showing a form with email and password fields and a Login button.](./img/c01-05.PNG "Member Login form")

5. Right-click the web page and choose **View Page Source**. You will see the HTML source code for the login page. Scroll down until the HTML `form` element is visible.

![View Page Source of the login page showing the HTML form element with input fields named "username" and "password".](./img/c01-06.PNG "Login form field names in the page source")

You can see the name of the form elements used to submit the username and password. The form element name properties are `username` and `password`. We will use these with `hydra` to brute force the page.

6. We need to supply to `hydra` with the text returned for an invalid login attempt. On the form, enter an invalid email and password and click **Login**. A message states: `Invalid email or password.`

![The Member Login form filled with an invalid email address and password just before clicking Login.](./img/c01-07.PNG "Submitting invalid login credentials")

![The login page displaying the failure message "Invalid email or password." after the failed login attempt.](./img/c01-08.PNG "Invalid login error message")

7. Using the information gathered in the steps above, run the command below to brute force the login.

```bash
sudo hydra -l jamie.johns@townsvillepool.pccc -P /home/user/passwords.txt townsville-pool.pccc http-post-form "/Home/Login:username=^USER^&password=^PASS^:Invalid email or password"
```

8. Review the successful password recovery result below.

![Kali terminal showing hydra completing the http-post-form brute force and reporting a valid login with the recovered password for the pool president account.](./img/c01-09.PNG "hydra recovers the president's password")

9. Log into the pool website with the following credentials:

- Email Address: `jamie.johns@townsvillepool.pccc`
- Password: `Hydrotherapy` (*Remember, the password is randomly selected upon challenge deployment. Your password will likely be different each time you launch this challenge.*)

Upon successful login with the pool president's credentials, Token 1 is displayed.

![The pool website home page after logging in as the president, with a green banner reading "Token 1: 4f389016" above the Townsville Community Pool heading.](./img/c01-10.PNG "Token 1 revealed after presidential login")

The correct submission for Question 1 is: `PCCC{login_Satisfied}`. Recall, this is an infinity-style question and the token will vary for your challenge instance.

## Question 2

*What is the value of token 2, which is awarded after you raise the temperature of the pool to 110 degrees Fahrenheit?*

1. Browse to `http://townsville-pool.pccc`. You may still have it open from solving Question 1.

2. Login as the pool president using the steps from Question 1. Notice the **Admin** link in the navigation bar. Click **Admin**.

![The pool website navigation bar with the Admin link visible now that the user is logged in as the pool president.](./img/c01-11.PNG "Admin link in the navigation bar")

3. The Admin Control Panel is where administrators raise or lower the pool temperature, but the system is limited to the range of *X to X* by the user interface control. This web page is set to auto-refresh every 60 seconds. As a result, you may see a popup window with a message similar to the following: "To display this page, Firefox must send information that will repeat any action (such as a search or order confirmation) that was performed earlier." It is safe to click the **Cancel** button.

![The Admin Control Panel page showing the pool temperature slider control and the Update Main Pool Temperature button.](./img/c01-12.PNG "Admin Control Panel temperature control")

![The Firefox popup warning that the page must resend previously submitted information, with a Cancel button that is safe to click.](./img/c01-12-2.PNG "Firefox resend-confirmation popup")

4. Open the web browser's developer tools and click the **Network** tab.

5. Use the slider to update the pool temperature, then click **Update Main Pool Temperature**.

6. Notice the `Authentication Error` message displayed at the top of the page. Additionally, in the **Network** tab in developer tools, a new `POST` message was added *after* you submitted the form. Right-click that message and choose **Edit and Resend** to see the details of the previous form post.

![The browser developer tools Network tab listing the POST request to AdminMain, with the right-click context menu open on the "Edit and Resend" option.](./img/c01-13.PNG "Edit and Resend the temperature POST request")

7. Scroll in the POST details to see the form `Body` contents.

![The Edit and Resend panel showing the request Body with the SetMainPoolTemperature value and empty AutomatedPoolManagementUsername and AutomatedPoolManagementPassword fields.](./img/c01-14.PNG "Temperature POST request body")

You should see something similar to the following content:

```text
SetMainPoolTemperature=89&AutomatedPoolManagementUsername=&AutomatedPoolManagementPassword=&Submit=Update+Main+Pool+Temperature
```

8. Notice that there are no values for the `AutomatedPoolManagementUsername` and `AutomatedPoolManagementPassword` form elements that were submitted. We need to find these values before we can POST a successful temperature update. Keep this browser tab open.

9. We already know from the challenge instructions that third-party websites can be found on the network. Let's start with an `nmap` scan.

```bash
nmap --dns-servers dns.pccc -sn $(ip route | grep "eth0" | grep -v default | awk '{print $1}')
```

The results show a website with a hostname that resolves to `apm.pccc`.

![Kali terminal showing nmap ping-sweep results that discover a host on the network resolving to the apm.pccc hostname.](./img/c01-15.PNG "nmap discovers the apm.pccc host")

10. Browse to `http://apm.pccc`. You have located the website of the Automated Pool Management Corporation.

![The Automated Pool Management Corporation website home page loaded at apm.pccc in the browser.](./img/c01-16.PNG "Automated Pool Management vendor site")

11. Browse the website. The **Home** and **About** pages don't provide any useful information, but the **Documentation** page contains a search form. Keep this website open for now.

![The Automated Pool Management Documentation page showing a search form for looking up product documentation.](./img/c01-17.PNG "Vendor Documentation search form")

12. Return to the pool website at `http://townsville-pool.pccc`. Click **Facilities**. In the list of facilities and future projects note the **Poolside_Innovations** project text:

> Poolside_Innovations
>
> We are adding advanced new technology throughout the pool grounds to enhance almost every aspect of your experience. We are currently working with a vendor named Automated Pool Management to install their Thermo Control System, Model No. 38119. This system will allow us to remotely monitor and control the temperature of all pools at our facility.

![The pool website's Facilities page listing current facilities and future projects.](./img/c01-18.PNG "Pool Facilities page")

![The Poolside_Innovations project description on the Facilities page, naming vendor Automated Pool Management and the Thermo Control System Model No. 38119.](./img/c01-19.PNG "Poolside_Innovations project mentions Model 38119")

13. The project description mentions Automated Pool Management and a Thermo Control System with a model number of 38119. Go back to the Automated Pool Management website and search for **38119**. You will find one result, the *Model 38119 Thermo Control Quick Start Guide*.

![The vendor Documentation search results for "38119" returning a single hit, the Model 38119 Thermo Control Quick Start Guide.](./img/c01-20.PNG "Search result for the Model 38119 Quick Start Guide")

14. Click the **Quick Start Guide** link. In the guide (38119.txt), note the Default Factory Control Credentials.

![The Model 38119 Thermo Control Quick Start Guide (38119.txt) open in the browser, showing the Default Factory Control Credentials username apmadmin and password 38119thermo.](./img/c01-21.PNG "Default factory credentials in the Quick Start Guide")

15. We will use these values to POST the form data to change the pool's temperature. Go back to the browser tab with the Admin Control Panel and the open developer tools.

16. We know from the challenge instructions that we must raise the temperature to at least 110 degrees. Modify the POST request **Body** to look like this:

```text
SetMainPoolTemperature=110&AutomatedPoolManagementUsername=apmadmin&AutomatedPoolManagementPassword=38119thermo&Submit=Update+Main+Pool+Temperature
```

17. Click **Send** to post the modified form data.

![The Edit and Resend Body edited to SetMainPoolTemperature=110 with the AutomatedPoolManagementUsername and AutomatedPoolManagementPassword fields filled in with the factory credentials, ready to click Send.](./img/c01-22.PNG "Resending the POST with temperature 110 and factory credentials")

18. At the bottom of the network traffic, select the most recent `POST`. Then select the **Response** tab, scroll through the content, and see Token 2!

![The developer tools Response tab for the resent POST showing the text "You have been awarded with Token 2: 884e3b9e".](./img/c01-23.PNG "Token 2 in the POST response")

Alternatively, double-click the latest `POST`. A new tab opens containing Token 2.

![A new browser tab opened from the POST showing the rendered Admin page with the Token 2 award message displayed.](./img/c01-24.PNG "Token 2 shown in a new tab")

The correct submission for Question 2 is: `PCCC{temp_Satisfied}`. Recall, this is an infinity-style question and the token will vary for your challenge instance.

## Question 3

*What is the value of token 3, which is awarded after you disable the security cameras on the pool website?*

1. Browse to `http://townsville-pool.pccc`. You may still have it open from solving Question 1 and Question 2. It does not matter if you are logged into the web site to complete this question.

2. Click **Live Cameras** to view the cameras. Here you see five pictures.

![The pool website's Live Cameras page showing five camera view images under the Live Camera Views heading.](./img/c01-25.PNG "Live Cameras page with five camera feeds")

3. Open the browser developer tools, select the **Network**  tab, then refresh the page. Note the five `GET` requests to `secapi.pccc`.

![The developer tools Network tab on the Live Cameras page showing five GET requests directed to the secapi.pccc camera API.](./img/c01-26.PNG "Five camera GET requests to secapi.pccc")

4. In a new browser tab, navigate to `http://secapi.pccc`. You are greeted with a Swagger API documentation page. Here you can interact with the API.

![The secapi.pccc Swagger UI API documentation page listing the available camera API endpoints.](./img/c01-27.PNG "Camera API Swagger documentation")

5. One of the APIs is called `disablecameras`. Expand the details for this API call.

![The Swagger UI with the disablecameras API endpoint expanded to show its details.](./img/c01-28.PNG "disablecameras endpoint expanded")

6. Click **Try it out**. The body expects some type of string value. It isn't clear *what* value is expected and the API is poorly documented. 

![The disablecameras endpoint after clicking Try it out, showing an editable request body pre-filled with a placeholder "string" value.](./img/c01-29.PNG "disablecameras request body with placeholder value")

7. Clear the `"string"` value and click **Execute**.

![The disablecameras response after executing with a cleared body, returning the error "The securityToken field is required."](./img/c01-30.PNG "securityToken required error")

The error message states: `"The securityToken field is required."` to POST to this API method. We haven't seen any traffic that contains a `securityToken` value so it's time to take a packet capture.

8. Open a terminal on your Kali VM and start a packet capture using `tcpdump`:

```bash
sudo tcpdump -i eth0 -w capture.pcap
```

9. While `tcpdump` is running, go back to the Live Cameras page and refresh the page. Then stop the capture with `Ctrl+C`.

10. Open the capture file in Wireshark:

```bash
wireshark capture.pcap
```

11. Filter by `http`. You should see an HTTP request that contains a `SecurityToken` query string value. Select this record and copy the value associated with the `SecurityToken`. Your output may be different, or you may have to inspect packets further. 
![Wireshark filtered on http, with a highlighted GET request to /api/getcamerastatus whose query string contains a securityToken value, and the full request URI shown in the packet detail pane.](./img/c01-38.PNG "SecurityToken captured in Wireshark")

An alternative to this is running:

```bash
sudo tcpdump -r capture.pcap -A | grep -i securityToken
```

12. Go back to the Swagger API at `http://secapi.pccc`. Enter the `SecurityToken` value into the form for the `disablecameras` API. Swagger will automatically format it as JSON, so enter the value without surrounding quotes.

![The disablecameras Swagger request body with the captured securityToken value entered, formatted as JSON without surrounding quotes.](./img/c01-39.PNG "securityToken entered in the disablecameras request")

13. Click **Execute**. Clicking Execute should produce an HTTP 200 success message with a return value of `true`.

![The disablecameras response showing an HTTP 200 success code with a return value of true.](./img/c01-40.PNG "disablecameras returns 200 true")

14. Go back to the Live Cameras page and refresh. If you successfully disabled the cameras, the pictures should not be visible, and Token 3 is shown.

![The Live Cameras page refreshed with the camera images gone and a green banner reading "Token 3: 98045a94".](./img/c01-41.PNG "Token 3 shown after cameras are disabled")

The correct submission for Question 3 is: `PCCC{camera_Satisfied}`. Recall, this is an infinity-style question and the token will vary for your challenge instance.

## Question 4

*What is the value of token 4, which is awarded after you change the pH, chlorine and total alkalinity values?*

1. Browse to `http://townsville-pool.pccc`. You may still have it open from solving the previous questions.

2. While logged in as the pool president, click **Pool Conditions**. The Pool Chemical Balancing System page shows various readings from the pool chemical balances. You are tasked with changing three water balance values:
   - Decrease the pH from 7.0 to 6.0
   - Increase the chlorine level from 3 ppm to 4 ppm
   - Decrease the total alkalinity from 100 ppm to 70 ppm

3. The Pool Conditions page is displaying real-time data from somewhere. Right-click the page and choose **View Page Source**. In the HTML source, you will find a comment left by the developers that reveals the SCADA data source — a Modbus server at `modbus.pccc` on port `502`, along with the holding register addresses used for pool chemical data.

4. We can get the Modbus server's IP address by running:

```bash
ping modbus.pccc
```

5. Double-click the **ctmodbus** shortcut on the Kali VM Desktop (or run `ctmodbus` in a terminal) and connect to the Modbus server using its IP address:

```bash
connect tcp <modbus.pccc-ip>
```

![The ctmodbus interactive console on the Kali VM after running "connect tcp" to establish a connection to the Modbus server at modbus.pccc.](./img/c01-45.PNG "Connecting to the Modbus server with ctmodbus")

6. The HTML comment told us that three holding registers contain the pool chemical data (HR0=pH, HR1=FAC, HR2=Alkalinity). Read the values in the holding registers. When you read the first three holding register values using the commands below, you will see that the values match the ones you need to change on the Pool Conditions web page.

```bash
read holdingRegisters 0
read holdingRegisters 1
read holdingRegisters 2
```

![The ctmodbus console reading holding register 0 (pH), showing the current value that matches the pH reading on the Pool Conditions page.](./img/c01-47.PNG "Reading the pH holding register")

![The ctmodbus console reading holding registers 1 (free available chlorine) and 2 (total alkalinity), showing values that match the Pool Conditions page.](./img/c01-48.PNG "Reading the chlorine and alkalinity holding registers")

Change these values with these  commands then refresh the Pool Conditions page. Use `ctmodbus` to change the values of the first three holding registers.

```bash
write register 0 6
write register 1 4
write register 2 70
```

![The ctmodbus console writing new values to holding registers 0, 1, and 2 (pH=6, chlorine=4, alkalinity=70) to change the pool chemical readings.](./img/c01-49.PNG "Writing new chemical values to the holding registers")

Refresh the `Pool Conditions` page. If you changed the correct values, Token 4 is displayed. Submit this token for Question 4.

![The refreshed Pool Conditions page showing the updated readings (pH 6, Total Alkalinity 70, Free Available Chlorine 4) with a green banner reading "Token 4: effd996e".](./img/c01-50.PNG "Token 4 shown after changing the water-balance values")

The correct submission for Question 4 is: `PCCC{scada_Satisfied}`. Recall, this is an infinity-style question and the token will vary for your challenge instance.
