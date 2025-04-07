import evdev
import select
from evdev import InputDevice, categorize, ecodes
import time

# Replace with the actual input device path (event0 or event1)
device = InputDevice('/dev/input/event0')  # You can change this to event1 if event0 doesn't work

# Grab the input device to prevent other processes from accessing it
device.grab()

# Create a poll object to check for events
poller = select.poll()
poller.register(device, select.POLLIN)

while True:
    # Wait for an event to be ready to read (with a timeout of 1 second)
    events = poller.poll(1000)  # Timeout in milliseconds (1000ms = 1 second)

    if events:
        for event in device.read():
            if event.type == ecodes.EV_KEY:
                if event.value == 1:  # Key press event
                    key_name = categorize(event)
                    print(f"Key {key_name} pressed")
                    if key_name.keycode == 'KEY_Q':
                        print('You pressed Q!')
                        device.ungrab()  # Release the device after the loop
                        break
    else:
        print("Waiting for input...")  # Debugging output
    time.sleep(0.1)  # Sleep to avoid high CPU usage during debugging
