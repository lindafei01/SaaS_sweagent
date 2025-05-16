
#!/usr/bin/env python3
import requests
import json

# Example email from the OpenAPI schema
example_email = """MIME-Version:1.0
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

# Example email with unsubscribe intent
unsubscribe_email = """MIME-Version:1.0
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

def test_endpoint(email_content):
    """Test the /decideUnsubscribe endpoint with the given email content"""
    url = "http://0.0.0.0:5000/decideUnsubscribe"
    headers = {"Content-Type": "text/plain"}
    
    try:
        response = requests.post(url, data=email_content, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    print("Testing with example email (no unsubscribe intent):")
    test_endpoint(example_email)
    
    print("\nTesting with email containing unsubscribe intent:")
    test_endpoint(unsubscribe_email)