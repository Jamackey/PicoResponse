# PicoResponse
 Python frequency reponse (bode plot) using the Pico 2000 series USB Oscilloscope.
  
### Usage/Installation:
1. Install **PicoSDK** from here: http://picotech.com/downloads _(select your device and choose 32/64-bit version)_
2. Install picosdk python wrapper via pypi by typing `pip install picosdk` into CMD
3. Git clone, or download and extract PicoResponse
4. Plug AWG/Siggen output into filter circuit on PicoScope, then output of filter into channel A
5. Run main.py by typing `python main.py` into CMD
 
<sub>Notes:  
Change frequency range and step in top of main.py  
Below 100 Hz PicoScope takes longer to capture  
Any issues, let me know!</sub>
___
### Device Compatability:
  - PicoScope 2000a Series 
  - PicoScope 3000a Series

### Tested Devices:
 - PicoScope 2408B
___
### PC Compatability:
 Only tested using Windows 10, using 64-bit PicoSDK 
___
### Todo:
- [ ] Test a PicoScope 3000a series
- [ ] Add support for PicoScope 5000 series
