copy message_gen\out\messages\__init__.py .\messages\__init__.py
copy message_gen\out\messages\MessageDeserializer.py .\messages\MessageDeserializer.py
copy message_gen\out\msg_codes.py .\msg_codes.py
robocopy /xc /xn /xo message_gen\out\messages .\messages
