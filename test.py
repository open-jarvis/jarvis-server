from classes.Crypto import Crypto
from classes.Communication import Communication


lorem = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. In placerat dui sed commodo rutrum. Donec pretium aliquam nulla. Maecenas ac purus sit amet lacus vehicula dictum. Vestibulum iaculis nisl vitae purus dapibus, sit amet sagittis purus imperdiet. Aliquam at enim sed massa faucibus congue non eget ante. Pellentesque feugiat nibh et tellus porta efficitur. In hac habitasse platea dictumst.
Donec mattis vehicula augue, sit amet laoreet metus eleifend sed. Nullam porttitor mollis mattis. Proin auctor nisi blandit, cursus lorem et, ullamcorper mi. Phasellus ac sapien sed lorem egestas commodo a a tortor. Curabitur condimentum turpis vel nulla condimentum dignissim. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Morbi eu cursus libero. Pellentesque consequat elementum risus id condimentum. Nullam sed viverra lectus, vel auctor ligula. Sed condimentum felis eu dolor finibus, vel rhoncus magna hendrerit. Fusce vitae ex porttitor, semper ex nec, molestie augue. Cras accumsan enim sed diam ultrices, at ultricies velit euismod. Mauris eu maximus nisi. Curabitur cursus massa sit amet dolor lobortis, eu imperdiet leo pretium.
Nunc eu interdum lorem. Praesent vehicula consequat quam, ut efficitur purus mattis id. Vivamus in iaculis nisi. Quisque elementum lacus vitae elementum maximus. Quisque vitae suscipit elit. In a mi dui. Proin mollis eros neque, at sagittis est mollis a.
Phasellus at sem elit. Aliquam suscipit, mi ut tempor aliquam, libero turpis tempor mauris, id luctus lectus risus eget eros. Sed eu commodo ex. Donec aliquet at odio in semper. Donec eleifend, orci eu convallis condimentum, purus velit congue nunc, in semper ligula magna sit amet velit. Nulla et erat nec mauris ornare mattis ut ac libero. Vivamus facilisis dignissim bibendum. Mauris consectetur, erat eget tincidunt ultricies, urna lorem bibendum diam, at imperdiet felis orci ut ligula.
Nullam pharetra tincidunt sollicitudin. Vivamus vitae maximus ex. Phasellus tincidunt, justo id hendrerit vehicula, dui lorem venenatis nisi, a hendrerit lectus justo ac ligula. Donec vehicula ornare est, nec euismod ligula luctus egestas. Duis ut purus lacinia diam rutrum cursus. In non massa sit amet mauris lobortis lacinia. Pellentesque elementum suscipit cursus. Etiam ex leo, vestibulum a lobortis quis, tempor et quam. Ut condimentum venenatis consectetur. Vivamus gravida iaculis interdum. Curabitur vitae lorem id odio volutpat suscipit. Nulla viverra aliquet arcu. Vivamus ultrices, arcu nec dictum viverra, purus nunc finibus quam, ac fermentum quam lorem at lorem. Sed molestie aliquet facilisis. Nunc malesuada purus mi, ut tristique lectus sagittis non.
"""


lpriv, lpub = Crypto.keypair(1024)
rpriv, rpub = Crypto.keypair(1024)
lkey, liv = Crypto.symmetric()
rkey, riv = Crypto.symmetric()
lcom = Communication(lpriv, lpub, rpub, lkey, liv)
rcom = Communication(rpriv, rpub, lpub, rkey, riv)
enc = lcom.encrypt(lorem, is_json=False)
print(enc)
dec = rcom.decrypt(enc, ignore_invalid_signature=False)
print(dec)
