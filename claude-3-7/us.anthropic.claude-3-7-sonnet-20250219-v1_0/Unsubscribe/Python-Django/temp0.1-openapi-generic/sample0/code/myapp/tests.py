
from django.test import TestCase, Client
import json
from django.urls import reverse

# Create your tests here.
class UnsubscribeTests(TestCase):
    def test_unsubscribe_endpoint_with_valid_email(self):
        """Test the unsubscribe endpoint with a valid email in the body"""
        client = Client()
        email_body = """MIME-Version:1.0
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
        
        response = client.post('/decideUnsubscribe', data=email_body, content_type='text/plain')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['email'], 'c@sigparser.com')
        self.assertTrue(data['unsubscribe'])
        
    def test_unsubscribe_endpoint_without_unsubscribe_request(self):
        """Test the unsubscribe endpoint with an email that doesn't request unsubscription"""
        client = Client()
        email_body = """MIME-Version:1.0
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

Ok. Just a thought. Got it.

--000000000000382db0057f0910d5"""
        
        response = client.post('/decideUnsubscribe', data=email_body, content_type='text/plain')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['email'], 'c@sigparser.com')
        self.assertFalse(data['unsubscribe'])