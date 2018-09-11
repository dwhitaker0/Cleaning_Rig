from Machines import Numato_Control as Numato 



Light_Source = Numato.UVLightSource("COM11")

Light_Source.halogen_on()
Light_Source.deuterium_on()