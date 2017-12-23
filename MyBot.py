"""
This bot's name is Tardigrade1.01.

Principles:
    - This will be a very simple bot
    - Our strategy will not change as the game progresses
    - We will focus only on docking on planets
    - We will choose which bots go to which planets using a probabilistic process
    - Nearby planets and large planets will be prioritised

Tactics:
For each undocked ship assign probability for all planets based on distance and size.
"""

import hlt
import logging
import math
import random


def calculate_ship_planet_coefficient(ship, planet):
    distance_to_planet = float(ship.calculate_distance_between(planet))
    planet_radius = float(planet.radius)
    return planet_radius/pow(distance_to_planet, 3)


def get_ship_planet_move(game_map, ship, planet):
    if planet.is_owned():
        if planet.owner == game_map.get_me():
            if planet.is_full():
                logging.info("bleh")
                return None
            else:
                if ship.can_dock(planet):
                    logging.info("Ship {} docking at planet {}".format(ship.id, planet.id))
                    return ship.dock(planet)
                else:
                    logging.info("Ship {} navigating to planet {}".format(ship.id, planet.id))
                    speed = min(hlt.constants.MAX_SPEED, math.ceil(planet.radius) + hlt.constants.DOCK_RADIUS - 1)
                    return ship.navigate(ship.closest_point_to(planet),
                                         game_map,
                                         speed=speed,
                                         ignore_ships=False,
                                         )
        else:
            # get a docked ship
            docked_ship = planet.all_docked_ships()[0]
            logging.info("Ship {} navigating to docked ship {}".format(ship.id, docked_ship.id))
            ignore_ships = True if ship.calculate_distance_between(docked_ship) < 8 else False
            return ship.navigate(docked_ship,
                                 game_map,
                                 speed=hlt.constants.MAX_SPEED,
                                 ignore_ships=ignore_ships,
                                 )

    else:
        if ship.can_dock(planet):
            logging.info("Ship {} docking at planet {}".format(ship.id, planet.id))
            return ship.dock(planet)
        else:
            logging.info("Ship {} navigating to unowned planet {}".format(ship.id, planet.id))
            return ship.navigate(ship.closest_point_to(planet),
                                 game_map,
                                 speed=hlt.constants.MAX_SPEED,
                                 ignore_ships=False,
                                 )


def get_new_target_and_move(game_map, ship):
    planets_and_coeffs = [
        (p, calculate_ship_planet_coefficient(ship, p))
        for p in game_map.all_planets()
        if p.owner != game_map.get_me() or not p.is_full()
    ]

    sum_of_coeffs = sum(coeff for _, coeff in planets_and_coeffs)
    planets_and_probs = [(p, coeff / sum_of_coeffs) for p, coeff in planets_and_coeffs]
    target = choose_new_target(planets_and_probs)
    move = get_ship_planet_move(game_map, ship, target)
    if move is None:
	    logging.warning("None command for ship {} and planet {}, which is full? {}".format(ship.id, target.id, target.is_full()))

    return target, move


def choose_new_target(planets_and_probs):
    # planets = [planet for planet, _ in planets_and_probs]
    # probs = [prob for _, prob in planets_and_probs]
    # return np.random.choice(planets, 1, p=probs)[0]

    deck = []
    for planet, prob in planets_and_probs:
        n = int(prob * 1000)
        deck.extend([planet] * n)

    random.shuffle(deck)
    return random.choice(deck)


game = hlt.Game("Tardigrade1")
last_targets = {}
turn = 0


while True:
    turn += 1
    logging.info("Starting turn {}".format(turn))
    game_map = game.update_map()
    me = game_map.get_me()

    logging.info(me.id)

    command_queue = []

    for ship in game_map.get_me().all_ships():
        if ship.docking_status != ship.DockingStatus.UNDOCKED:
            continue

        last_target = last_targets.get(ship.id, None)

        if last_target is not None:
            logging.info("Found existing move for ship {} to planet {}".format(ship.id, last_target.id))
            move = get_ship_planet_move(game_map, ship, last_target)
            if move is not None:
                command_queue.append(move)
                continue

        target, move = get_new_target_and_move(game_map, ship)
        if move is None:
            move = ship.thrust(0, ship.calculate_angle_between(target))
        logging.info("Making new move for ship {} to {}".format(ship.id, target))
        last_targets[ship.id] = target
        command_queue.append(move)

    game.send_command_queue(command_queue)
