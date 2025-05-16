
import requests

# Example email from the OpenAPI spec
test_email = """MIME-Version:1.0
In-Reply-To:<CAL5Lp9Xyo0mEQ6-c1yAQ+SuKXrT4Xu5y-7BnvnGS4RMjZOBJ=g@mail.gmail.com>
From:Chris <c@sigparser.com>
Date:Wed, 9 Jan 2019 08:36:15 -0800
Message-ID:<CABxEEoizOPyCLkq4+FBGNaw7KC2TJDfTZF5dp8xD9aFjDQoL+Q@mail.gmail.com>
Subject:Re:food for thought
To:Paul <p@sigparser.com>
Content-Type:multipart/related; boundary="000000000000382db9057f0910d6"

--000000000000382db9057f0910d6
Content-Type:multipart/alternative; boundary="000000000000382db0057f0910d5"

--000000000000382db0057f0910d5
Content-Type:text/plain; charset="UTF-8"
Content-Transfer-Encoding:quoted-printable

Ok.  Just a thought.  Got it.

--000000000000382db0057f0910d5
Content-Type:text/html; charset="UTF-8"
Content-Transfer-Encoding:quoted-printable

<div><div dir=3D"auto">Ok.=C2=A0 Just a thought.=C2=A0 Got it. =C2=A0</div>=
</div><div><br><div class=3D"gmail_quote"><div dir=3D"ltr">On Wed, Jan 9, 2="""

# Test email with unsubscribe intent
test_email_unsubscribe = """MIME-Version:1.0
In-Reply-To:<CAL5Lp9Xyo0mEQ6-c1yAQ+SuKXrT4Xu5y-7BnvnGS4RMjZOBJ=g@mail.gmail.com>
From:Chris <c@sigparser.com>
Date:Wed, 9 Jan 2019 08:36:15 -0800
Message-ID:<CABxEEoizOPyCLkq4+FBGNaw7KC2TJDfTZF5dp8xD9aFjDQoL+Q@mail.gmail.com>
Subject:Re:food for thought
To:Paul <p@sigparser.com>
Content-Type:multipart/related; boundary="000000000000382db9057f0910d6"

--000000000000382db9057f0910d6
Content-Type:multipart/alternative; boundary="000000000000382db0057f0910d5"

--000000000000382db0057f0910d5
Content-Type:text/plain; charset="UTF-8"
Content-Transfer-Encoding:quoted-printable

Please unsubscribe me from this mailing list. Thanks.

--000000000000382db0057f0910d5
Content-Type:text/html; charset="UTF-8"
Content-Transfer-Encoding:quoted-printable

<div><div dir=3D"auto">Please unsubscribe me from this mailing list. Thanks.=C2=A0</div>=
</div><div><br><div class=3D"gmail_quote"><div dir=3D"ltr">On Wed, Jan 9, 2="""

def test_endpoint(email_content, expected_unsubscribe=False):
    """Test the /decideUnsubscribe endpoint with the given email content."""
    try:
        # Send the email content to the endpoint
        response = requests.post(
            "http://0.0.0.0:5000/decideUnsubscribe",
            data=email_content,
            headers={"Content-Type": "text/plain"}
        )
        
        # Check if the response is successful
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result}")
            
            # Check if the email address was extracted correctly
            if result.get("email") == "c@sigparser.com":
                print("✓ Email address extracted correctly")
            else:
                print(f"✗ Email address extraction failed. Expected: c@sigparser.com, Got: {result.get('email')}")
            
            # Check if the unsubscribe decision is as expected
            if result.get("unsubscribe") == expected_unsubscribe:
                print(f"✓ Unsubscribe decision is correct: {expected_unsubscribe}")
            else:
                print(f"✗ Unsubscribe decision is incorrect. Expected: {expected_unsubscribe}, Got: {result.get('unsubscribe')}")
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

# Note: These tests will only work when the FastAPI app is running
print("Note: Make sure the FastAPI app is running before executing these tests.")
print("\nTest 1: Regular email (no unsubscribe intent)")
print("----------------------------------------------")
test_endpoint(test_email, expected_unsubscribe=False)

print("\nTest 2: Email with unsubscribe intent")
print("------------------------------------")
test_endpoint(test_email_unsubscribe, expected_unsubscribe=True)