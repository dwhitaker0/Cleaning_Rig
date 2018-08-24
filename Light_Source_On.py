from Machines import Numato_Control as Numato 



Light_Source = Numato.UVLightSource("COM9")

Light_Source.halogen_on()
Light_Source.deuterium_on()