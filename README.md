This program requires a Raspberry Pi, movement detector and a microphone to function.
We recommend using pin 24 for the movement detector output, connecting it to another pin would require a small change in programs code from user.

To install needed dependencies please enter following commands in your Raspberry Pi terminal
```
xargs sudo apt install -y < packages.txt
pip3 install -r requirements.txt
```