def resolve_rpc(player1_choice, player2_choice):
    """
    Determines the attacker based on Rock-Paper-Scissors.
    Returns 'player1', 'player2', or 'tie'.
    """
    if player1_choice == player2_choice:
        return 'tie'
    
    # Define the winning scenarios for Player 1
    p1_wins = (
        (player1_choice == 'rock' and player2_choice == 'scissors') or
        (player1_choice == 'scissors' and player2_choice == 'paper') or
        (player1_choice == 'paper' and player2_choice == 'rock')
    )
    
    if p1_wins:
        return 'player1'
    else:
        return 'player2'

def calculate_damage(attacker_element, defender_element):
    """
    Calculates damage based on Fate element matchups.
    Water beats Fire, Fire beats Leaf, Leaf beats Water.
    """
    if attacker_element == defender_element:
        return 2 # Same element clashes deal 2 damage
        
    # Define when the Attacker has the elemental advantage
    attacker_advantage = (
        (attacker_element == 'water' and defender_element == 'fire') or
        (attacker_element == 'fire' and defender_element == 'leaf') or
        (attacker_element == 'leaf' and defender_element == 'water')
    )
    
    if attacker_advantage:
        return 3 # Advantage deals maximum damage (3)
    else:
        return 1 # Disadvantage means the attack is weak (1)