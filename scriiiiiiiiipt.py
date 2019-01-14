import neopixel
import code

from led_tools import player

strip = neopixel.Adafruit_NeoPixel(300, 21, strip_type=neopixel.ws.WS2811_STRIP_GRB)
strip.begin()

p = player.Player(strip, 60)
p.set_mode(p.MODE_ANIMATION)

p.add_anim('anim:test:0001;area:1001;ticks:60;color:gradient:random:random;movement:move:linear:-:300',
           'default',
           'delay:0')

code.interact(local=locals())