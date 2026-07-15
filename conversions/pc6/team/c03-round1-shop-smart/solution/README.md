# Shop SMart

*Solution Guide*

## Overview

The purpose of this challenge is to attack the S-Mart e-commerce website using [OWASP Top Ten vulnerabilities](https://owasp.org/www-project-top-ten/) to recover four (4) tokens.

Browse to `http://shop-smart`.

## Question 1

*Enter the token received from logging in as an admin user.*

**Vulnerability:** Broken Access Control — the registration form passes `is_admin=0` as a GET parameter that the server trusts without validation.

1. Open Burp Suite and choose the defaults until you come to the Learn tab.

	![Screenshot of the Burp Suite Community Edition Learn tab, showing "Learn, explore and discover" cards such as Getting started, video tutorials, and the Web Security Academy.](imgs/img1.png "Burp Suite opened to the Learn tab")

2. Select **Proxy**, **Open browser** in the Proxy tab. Browse to `http://shop-smart` in the Burp browser.

	![Screenshot of the Burp Suite Proxy Intercept tab with "Intercept is off" displayed and the orange "Open browser" button highlighted.](imgs/img2.png "Launching Burp's browser from the Proxy tab")

3. In Burp, select the **HTTP history** tab. In the Burp browser, browse to the **REGISTER** tab, then in the HTTP history window, select the URL for `/register.php`.

	![Screenshot of Burp Suite HTTP history with the GET /register.php entry selected, showing the request and the response HTML for the registration page.](imgs/img3.png "Selecting the /register.php request in HTTP history")

4. Create a user on the **REGISTER** tab. We used *blah* for the username and some random information for the password and email. Note the new address added to HTTP history.

	![Screenshot of Burp Suite HTTP history showing the new POST /register.php?is_admin=0 entry, with the request body username=BLAH&password=DFFDF&email=... visible in the Request pane.](imgs/img4.png "The POST register request captured in HTTP history")

5. Right-click the left panel in Burp (**Request**) and select **Send to Repeater**. Note that the Repeater tab is highlighted. Select it. The left pane should look something like what's pictured below.

	![Screenshot of the Burp Suite Repeater Request pane showing POST /register.php?is_admin=0 with the body line username=BLAH&password=DFFDF at the bottom, ready to edit.](imgs/img5.png "The registration request loaded into Repeater")

6. The very first line is sending the command with the parameter `is_admin=0`. Change that to `is_admin=1`. The last line starting with `username` is the user you attempted to register. Change them to something you'll remember such as `username=tartan&password=password` and click **Send**.

7. After clicking **Send**, the right pane populates. If you select **Render**, you will see the page indicates registration successful!

	![Screenshot of Burp Repeater after sending POST /register.php?is_admin=1 with username=tartan&password=password; the Response Render pane shows the S-Mart register page with a green "Registration successful!" banner.](imgs/img6.png "Admin registration succeeds with is_admin=1")

8. Return to the browser, go to the **Login** page, and log in with your newly created administrator account. You should see a welcome message and the first token.

	![Screenshot of the S-Mart home page after logging in, reading "WELCOME TO S-MART, TARTAN" and "YOU ARE LOGGED IN AS AN ADMIN, HERE IS YOUR TOKEN: 8D26BD9D".](imgs/img7.png "Token 1 revealed on the admin welcome page")

>**Note!** The tokens are randomized, so your answer will be different than what is pictured.

## Question 2

*Enter the token from bcampbell's order history.*

**Vulnerability:** Weak credentials — the user `bcampbell` has a password that can be brute-forced using the wordlist on kali.

1. Log out of any current session.

2. Attempt to log in as `bcampbell` with any password. The error message says "Invalid password." — this confirms the user exists.

   ![Screenshot of the S-Mart login page at 10.5.5.100/login.php showing a red "Invalid password." error banner above the username and password fields, confirming the bcampbell account exists.](imgs/img8.png "Invalid password error confirms bcampbell exists")

3. Use the wordlist at `/home/user/wordlist.txt` on kali.

4. Use Hydra to brute-force the login:

```bash
hydra -t 4 -l bcampbell -P /home/user/wordlist.txt shop-smart http-post-form "/login.php:username=bcampbell&password=^PASS^:Invalid password."
```

5. Hydra discovers the password is `operating`.

   ![Screenshot of a Kali terminal running Hydra against shop-smart; the http-post-form result line reads "host: shop-smart login: bcampbell password: operating" and reports 1 valid password found.](imgs/img9.png "Hydra recovers the password: operating")

6. Log in as `bcampbell` / `operating` and navigate to **MY ORDERS**. **Token 2** is displayed on the page.

   ![Screenshot of the S-Mart MY ORDERS page for bcampbell, showing "Token = 664279d3" highlighted above an order row (Order ID 20, dated 2024-07-19, total 101.60) with a Download link.](imgs/img10.png "Token 2 displayed on bcampbell's orders page")

## Question 3

*Enter the value of the token3.txt file found in the /var/www/ directory.*

**Vulnerability:** Path Traversal — the `download.php` file directly uses user-supplied file paths without sanitization.

1. Log into the site with any account and click **MY ORDERS**.

2. Examine the **Download** link next to any order. The URL is: `http://shop-smart/download.php?file=invoices/order_XX.pdf`.

3. The `file` parameter is passed directly to `readfile()` without validation. Change the URL to:

```
http://shop-smart/download.php?file=/var/www/token3.txt
```

4. A file download is triggered containing **Token 3**.

## Question 4

*Enter the token for checking out with the chainsaw.*

**Vulnerability:** SQL Injection — the product search page concatenates user input directly into SQL queries.

1. Browse to the **PRODUCT SEARCH** page. Searching for `chainsaw` returns "No products found." — the chainsaw product exists in the database but is hidden (`is_visible = 0`).

2. Perform a SQL injection by entering the following into the search box:

```
' OR 1=1#
```

3. This returns all products in the database, including the hidden chainsaw.

   ![Screenshot of the S-Mart product search page with `' OR 1=1#` in the search box, under the heading "SEARCH RESULTS FOR ' OR 1=1#", now listing multiple product cards that the normal search would not return.](imgs/img11.png "SQL injection returns every product")

4. Scroll to the bottom of the results to find the Chainsaw product.

   ![Screenshot of the bottom of the injected search results showing the hidden Chainsaw product card, priced $199.99, described as "A powerful chainsaw suitable for various cutting tasks and capable of holding off the forces of evil," with a View link.](imgs/img12.png "The hidden Chainsaw product appears in the results")

5. Click **View** on the Chainsaw product page, then click **Add to Cart**.

   ![Screenshot of the Chainsaw product detail page showing the chainsaw photo, description, Price $199.99, a Quantity field, and an "Add to Cart" button.](imgs/img13.png "Adding the Chainsaw to the cart")

6. From the Shopping Cart, click **Proceed to Checkout**.

   ![Screenshot of the S-Mart SHOPPING CART page listing the Chainsaw at $199.99 with Update and Remove buttons and a "Proceed to Checkout" link.](imgs/img14.png "The Chainsaw in the shopping cart")

7. Click **Place Order**. The checkout page displays **Token 4** because the cart contains a hidden product.

   ![Screenshot of the S-Mart CHECKOUT page showing the Chainsaw order line, a Total of $199.99, a Place Order button, and "TOKEN: 9e73537f" displayed below.](imgs/img15.png "Token 4 shown on checkout for the hidden Chainsaw")
