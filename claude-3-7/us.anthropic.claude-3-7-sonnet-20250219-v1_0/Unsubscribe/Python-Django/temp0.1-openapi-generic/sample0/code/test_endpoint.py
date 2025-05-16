
import requests
import json

def test_unsubscribe_endpoint():
    """Test the unsubscribe endpoint with different email contents"""
    
    # Test case 1: Email with unsubscribe request
    email_with_unsubscribe = """MIME-Version:1.0
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

Please unsubscribe me from this list.

--000000000000382db0057f0910d5"""
    
    # Test case 2: Email without unsubscribe request
    email_without_unsubscribe = """MIME-Version:1.0
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

--000000000000382db0057f0910d5"""
    
    # Start the server in the background (this would be done separately)
    # Test the endpoint with unsubscribe request
    try:
        response1 = requests.post(
            'http://localhost:5000/decideUnsubscribe',
            data=email_with_unsubscribe,
            headers={'Content-Type': 'text/plain'}
        )
        
        print("Test 1 (with unsubscribe request):")
        print(f"Status code: {response1.status_code}")
        print(f"Response: {response1.json()}")
        print()
        
        # Test the endpoint without unsubscribe request
        response2 = requests.post(
            'http://localhost:5000/decideUnsubscribe',
            data=email_without_unsubscribe,
            headers={'Content-Type': 'text/plain'}
        )
        
        print("Test 2 (without unsubscribe request):")
        print(f"Status code: {response2.status_code}")
        print(f"Response: {response2.json()}")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the Django server is running on port 5000.")

if __name__ == "__main__":
    print("This script tests the unsubscribe endpoint.")
    print("Make sure to run the Django server first with: python manage.py runserver 0.0.0.0:5000")
    print("Then run this script in a separate terminal.")
    print()
    test_unsubscribe_endpoint()