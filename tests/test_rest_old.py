import unittest
import os
import json
import time
from telapi import rest

class TestREST(unittest.TestCase):
    def setUp(self):
        # Environment variables must be set for TELAPI_ACCOUNT_SID and TELAPI_AUTH_TOKEN
        self.client = rest.Client(base_url='https://api.telapi.com/v1/', account_sid='AC5521767e53d04deeb0a06f660cee50f9', auth_token='25cda66b744841f3a95be3b9e7b29ba7')

        # self.client = rest.Client()
        self.test_number = '+12133483023'


    # Test REST Client getattr
    def test_bad_resource_list_resource(self):
        with self.assertRaises(AttributeError):
            self.client.bad_resource_name

    def test_bad_credentials_account(self):
        with self.assertRaises(rest.exceptions.AccountSidError):
            rest.Client(account_sid='abc123')

    def test_bad_credentials_token(self):
        with self.assertRaises(rest.exceptions.AuthTokenError):
            rest.Client(account_sid='AC5521767e53d04deeb0a06f660cee50f9', auth_token='abc123')

    def test_account_list_resource(self):
        accounts = self.client.accounts
        self.assertEquals(accounts.__class__.__name__, 'AccountListResource')
        self.assertEquals(accounts._url, 'Accounts')

        # Make sure the list resource doesn't have instance resource params
        with self.assertRaises(AttributeError):
            accounts.sid

        # Bad property name
        with self.assertRaises(AttributeError):
            accounts.random_property_name

        # Dict-style key access
        account = accounts[self.client.account_sid]

        # Check types and generated URLs
        self.assertEquals(account.__class__.__name__, 'Account')
        self.assertEquals(account._url, 'Accounts/' + self.client.account_sid)
        self.assertEquals(account.sid, self.client.account_sid)
        self.assertEquals(account.status, 'active')

    def test_notifications_list_resource(self):
        account = self.client.accounts[self.client.account_sid]
        notifications = account.notifications
        print notifications
        self.assertEquals(notifications.__class__.__name__, 'NotificationListResource')

        # len()
        self.assertTrue(len(notifications))

        # Negative Indexes
        notifications[-1]

        # Iteration
        for notification in notifications:
            notification.request_url

        # Slicing
        for notification in notifications[10:20]:
            notification.request_url

        for notification in notifications[1:5:-1]:
            notification.request_url

        # Disallow setattr
        with self.assertRaises(TypeError):
            notifications[0] = 5

    def test_pagination(self):
        test_dir = os.path.dirname(__file__)
        accounts_data = json.load(open(os.path.join(test_dir, 'test_accounts.json')))

        # Internal call to use dummy data
        accounts = self.client.accounts[10:20]
        accounts.fetch(resource_data=accounts_data)

        for i, account in enumerate(accounts):
            self.assertIsNotNone(account.sid)

        self.assertEquals(i, 9)

        # Internal call to use dummy data
        accounts = self.client.accounts[20:40]
        accounts.fetch(resource_data=accounts_data)

        for i, account in enumerate(accounts):
            self.assertIsNotNone(account.sid)

        self.assertEquals(i, 19)

    def test_sms_list(self):
        sms_list = self.client.accounts[self.client.account_sid].sms_messages[:100]

        for i, sms in enumerate(sms_list):
            self.assertTrue(sms.body)
            self.assertTrue(sms.from_number)
            self.assertTrue(sms.to_number)

        self.assertEquals(i + 1, len(sms_list))

    def test_sms_filter(self):
        sms_list = self.client.accounts[self.client.account_sid].sms_messages.filter(To='+12133483023')[:100]

        for i, sms in enumerate(sms_list):
            self.assertTrue(sms.body)
            self.assertTrue(sms.from_number)
            self.assertTrue(sms.to_number)

        self.assertEquals(i + 1, len(sms_list))

    def test_sms_send(self):
        sms_list = self.client.accounts[self.client.account_sid].sms_messages
        from_number = to_number = self.test_number
        body = "Hello from telapi-python!"
        sms = sms_list.create(from_number=from_number, to_number=to_number, body=body)
        self.assertTrue(sms.sid.startswith('SM'))
        self.assertEquals(sms.body, body)
        self.assertEquals(sms.from_number, from_number)
        self.assertEquals(sms.to_number, to_number)

    def test_incoming_phone_numbers(self):
        account = self.client.accounts[self.client.account_sid]

        # Test listing
        for number in account.incoming_phone_numbers:
            print number.phone_number
            self.assertTrue(number.phone_number.startswith('+'))


        # Make sure there's no exception when there's no results
        no_available_numbers = account.available_phone_numbers.filter(AreaCode=999)
        # self.assertEquals(len(no_available_numbers), 0)

        for number in no_available_numbers:
            print no_available_numbers.phone_number


        # Filter and buy a DID
        available_numbers = account.available_phone_numbers.filter(AreaCode=435)
        self.assertTrue(len(available_numbers))

        for number in available_numbers:
            self.assertEquals(number.phone_number[:5], '+1435')
            self.assertEquals(number.npa, "435")
            self.assertEquals(number.country_code, "+1")

        good_available_number = available_numbers[0]
        phone_number = good_available_number.phone_number
        purchase_number = account.incoming_phone_numbers.create(phone_number=phone_number)


        # Try to update
        purchase_number.voice_url = voice_url = "http://db.tt/YtLJgpa8"
        purchase_number.save()


        # Make sure the number is in the list (clear the cache with .clear first)
        found = False
        
        for number in account.incoming_phone_numbers.clear():
            if number.phone_number == phone_number and number.voice_url.strip() == voice_url:
                found = True
                break

        self.assertTrue(found)


        # Delete the number
        purchase_number.delete()


        # Make sure the number is no longer in the list
        found = False
        for number in account.incoming_phone_numbers:
            if number.phone_number == phone_number and number.voice_url == voice_url:
                found = True
                break

        self.assertTrue(not found)

    def test_calls(self):
        account = self.client.accounts[self.client.account_sid]

        # Typecast to list to make sure enumeration works
        list(account.calls)

        # Use alternate syntax to create to update properties before saving
        call = account.calls.new()
        call.from_number = "+15552660933"
        call.to_number = "+12133483023"
        call.url = "https://dl.dropbox.com/u/14573179/InboundXML/wait_music.xml"

        # Dial
        call.save()

        # Wait a bit
        time.sleep(20)

        # Hangup
        call.status = "Completed"
        call.save()

    def test_call_dtmf(self):
        account = self.client.accounts[self.client.account_sid]

        # Use alternate syntax to create to update properties before saving
        call = account.calls.new()
        call.from_number = "+15552660933"
        call.to_number = "+12133483023"
        call.url = "https://dl.dropbox.com/u/14573179/InboundXML/wait_music.xml"

        # Dial
        call.save()

        # Wait a bit
        time.sleep(40)

        # Play DTMF on b leg
        call.play_dtmf = "1*2#3w456ww789"
        call.play_dtmf_leg = "bleg"
        call.save()

    def test_call_play_sound(self):
        account = self.client.accounts[self.client.account_sid]

        # Use alternate syntax to create to update properties before saving
        call = account.calls.new()
        call.from_number = "+15552660933"
        call.to_number = "+12133483023"
        call.url = "https://www.telapi.com/data/inboundxml/8d4f80df0d37819cde3e3d2bb9982d111ebac97c"

        # Dial
        call.save()

        # Wait a bit
        time.sleep(20)

        # Play sounds
        play = call.plays.new()
        play.audio_url = "https://dl.dropbox.com/u/14573179/Audio/Freeswitch/sounds/en/us/callie/misc/8000/sorry.wav,https://dl.dropbox.com/u/14573179/Audio/Freeswitch/sounds/en/us/callie/misc/8000/call_secured.wav"
        play.mix = False
        play.legs = 'aleg'
        play.save()


    def test_call_voice_warp(self):
        account = self.client.accounts[self.client.account_sid]

        # Use alternate syntax to create to update properties before saving
        call = account.calls.new()
        call.from_number = "+15552660933"
        call.to_number = "+12133483023"
        call.url = "https://www.telapi.com/data/inboundxml/8d4f80df0d37819cde3e3d2bb9982d111ebac97c"

        # Dial
        call.save()

        # Wait a bit
        time.sleep(10)

        # Start Effect
        effect = call.effects.new()
        effect.pitch = .5
        effect.save()

    def test_call_record(self):
        account = self.client.accounts[self.client.account_sid]

        # Use alternate syntax to create to update properties before saving
        call = account.calls.new()
        call.from_number = "+15552660933"
        call.to_number = "+12133483023"
        call.url = "https://dl.dropbox.com/u/14573179/InboundXML/pause.xml"

        # Dial
        call.save()

        # Wait a bit
        time.sleep(10)

        # Start recording
        recording = call.recordings.new()
        recording.record = True
        recording.callback_url = "http://liveoutput.com/hHWXvdf7"
        recording.time_limit = 60
        recording.save()

        time.sleep(10)

        # Start recording
        call.recordings.new(record=False).save()

    def test_call_autotune(self):
        account = self.client.accounts[self.client.account_sid]

        # Use alternate syntax to create to update properties before saving
        call = account.calls.new()
        call.from_number = "+15555555555"
        call.to_number = self.test_number
        call.url = "https://www.telapi.com/data/inboundxml/8d4f80df0d37819cde3e3d2bb9982d111ebac97c"

        # Dial
        call.save()

        # Wait a bit
        time.sleep(15)

        # Start Effect
        effect = call.effects.new()
        effect.autotune_tune = -1
        effect.autotune_shift = 12
        effect.save()

    def test_call_redirect(self):
        account = self.client.accounts[self.client.account_sid]

        # Use alternate syntax to create to update properties before saving
        call = account.calls.new()
        call.from_number = "+15552660933"
        call.to_number = self.test_number
        call.url = "http://dl.dropbox.com/u/xxxx/sound.xml"

        # Dial
        call.save()

        # Wait a bit
        time.sleep(15)

        # Redirect
        call.url = 'http://dl.dropbox.com/u/xxxx/redirect.xml'
        call.save()

    def test_cnam_lookup(self):
        cnam_list = self.client.accounts[self.client.account_sid].cnam_dips.filter(PhoneNumber=self.test_number)

        for i, cnam in enumerate(cnam_list):
            self.assertTrue(cnam.body)
            self.assertEquals(cnam.phone_number, self.test_number)

        self.assertEquals(len(cnam_list), 1)

    def test_call_by_sid(self):
        calls = self.client.accounts[self.client.account_sid].calls
        sid = 'AC5521767e53d04deeb0a06f660cee50f9'

        # Straight up get by sid
        call = calls[sid]
        self.assertTrue(call)

        # Prefetched
        for call in calls:
            pass
        call = calls[sid]
        self.assertTrue(call)

if __name__ == '__main__':
    unittest.main()