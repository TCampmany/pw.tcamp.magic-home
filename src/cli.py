import argparse
from enum import Enum, auto

from src import MagicHome


class MagicHomeActions(Enum):
    LIST = auto()
    ON = auto()
    OFF = auto()
    TOGGLE = auto()
    COLOR = auto()


def generate_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Interact with MagicHome LED controllers.')

    controller = parser.add_argument_group("Controller selection")
    controller_group = controller.add_mutually_exclusive_group()
    controller_group.add_argument("--discover", "-d", dest='addr', action="store_const", default=None, const=None,
                                  help="Will discover all MagicHome controllers in the network.")
    controller_group.add_argument("--addr", "-a", nargs="+",
                                  help="Specify the address of one or more controllers.")

    actions = parser.add_argument_group("Actions")
    a = actions.add_mutually_exclusive_group()
    a.add_argument("--list", "-l", dest='action', action="append_const", const=MagicHomeActions.LIST)
    a.add_argument("--on", dest='action', action="append_const", const=MagicHomeActions.ON)
    a.add_argument("--off", dest='action', action="append_const", const=MagicHomeActions.OFF)
    a.add_argument("--toggle", dest='action', action="append_const", const=MagicHomeActions.TOGGLE)
    a.set_defaults(action=[MagicHomeActions.LIST])

    parser.add_subparsers()
    a.add_argument("--color", dest='action', action="append_const", const=MagicHomeActions.TOGGLE)

    return parser


parser = generate_parser()
args = parser.parse_args()

if args.addr is None:
    controllers = list(MagicHome.discover())
else:
    controllers = []
    for addr in args.addr:
        controllers.append(MagicHome.connect(addr))

if MagicHomeActions.LIST in args.action:
    print(f"{'Address':<20}|{'ID':<16}|{'Model':<16}")
    print(f"{'':-<20}+{'':-<16}+{'':-<16}")
    for controller in controllers:
        print(f"{controller.addr:<20}|{controller.id:<16}|{controller.model:<16}")

if MagicHomeActions.ON in args.action:
    for controller in controllers:
        controller.turn_on()

if MagicHomeActions.TOGGLE in args.action:
    for controller in controllers:
        controller.power_toggle()

if MagicHomeActions.COLOR in args.action:
    for controller in controllers:
        controller.color(r, g, b, w)

if MagicHomeActions.OFF in args.action:
    for controller in controllers:
        controller.turn_off()

# print(args)

#
#
# states = []
# for x in range(0, -255, -8):
#     states.append(MagicHomeControllerState(True, MagicHomeControllerColorState(254, 166, 87, 0).change_brightness(x)))
#
# c = MagicHome.connect('192.168.68.240')
# print(c)
# for state in states:
#     print(state)
#     c.state = state
#     sleep(1)
#
# c.turn_on()
# c.power_toggle()
# c.power_toggle()
# c.turn_off()
