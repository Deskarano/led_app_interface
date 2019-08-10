import neopixel
import code

from led_tools import player

strip = neopixel.Adafruit_NeoPixel(300, 21, strip_type=neopixel.ws.WS2811_STRIP_GRB)
strip.begin()

p = player.Player(strip, 60)
p.set_mode(p.MODE_ANIMATION)

p.add_anim('anim:gentle alarm:vUmshFyguQTSfLiO;area:DP9uNl4yxTQ6ZQRE;ticks:1311;color:gradient:0x11AC6F:0xE8C55E;movement:move:Linear:-:200',
           'event:blah;conf0:now',
           'event:meh;conf0:never',
           'event:meh;conf0:never')

code.interact(local=locals())