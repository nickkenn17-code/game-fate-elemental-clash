def resolve_rpc(p1_choice, p2_choice):
    """Determines the winner of the priority phase."""
    winning_moves = {'rock': 'scissors', 'paper': 'rock', 'scissors': 'paper'}
    
    if p1_choice == p2_choice:
        return 'tie'
    elif winning_moves.get(p1_choice) == p2_choice:
        return 'player1'
    else:
        return 'player2'

def calculate_combat(attacker_element, defender_element):
    """
    Calculates the HP deduction based on the Elemental Triangle.
    Returns: (damage_to_defender, damage_to_attacker)
    """
    # 1. Elemental Tie
    if attacker_element == defender_element:
        return (10, 0) # Only the attacker deals 10 damage

    # 2. Attacker Advantage (Critical Hit)
    # Notice we updated 'earth' to 'leaf' to perfectly match your React UI!
    advantage = {
        'fire': 'leaf',
        'leaf': 'water',
        'water': 'fire'
    }
    
    if advantage.get(attacker_element) == defender_element:
        return (35, 0) # Attacker deals 35 damage

    # 3. Defender Advantage (Counter-Attack)
    return (0, 20) # Attacker takes 20 damage