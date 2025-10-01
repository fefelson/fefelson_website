from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse

def send_user_email(user, games):
    if not games:
        return False

    # Plain text version
    subject = "FE.Felson - Player's Edge"
    body_lines = [f"Hi {user.username},\n\nToday's best bets (up to 5 games):\n"]
    html_lines = [
        f"""
        <html>
        <body style="font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2c3e50;">Hi {user.username},</h2>
        <p style="font-size: 16px;">Today's best bets (up to 5 games):</p>
        """
    ]

    for i, game_data in enumerate(games[:5]):  # Limit to 5 games
        game = game_data["game"]
        bet_side = game_data["bet_side"]
        edge_value = game_data["edge_value"]
        ml = f"+{game_data['ml']}" if game_data['ml'] > 0 else game_data['ml']
        implied_prob = game_data["implied_prob"]
        wager = game_data["wager"]

        if bet_side == "none":
            continue

        team_to_bet = game.home_team.organization.abrv if bet_side == "home" else game.away_team.organization.abrv
        formatted_date = game.game_date.strftime("%A, %B %-d")

        # Plain text
        body_lines.append(
            f"- {formatted_date}\n"
            f"  League: {game.league.name}\n"
            f"  Match: {game.away_team.organization.first_name} vs {game.home_team.organization.first_name}\n"
            f"  Bet: {team_to_bet} ({ml})\n"
            f"  Probability: {(edge_value + implied_prob):.2f}% chance\n"
            f"  Wager: ${wager:.2f}\n"
        )

        # HTML with individual boxes, alternating background colors, and hover effect
        box_bg = "#f9f9f9" if i % 2 == 0 else "#ffffff"
        html_lines.append(
            f"""
            <div style="background-color: {box_bg}; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: background-color 0.3s;">
                <p style="margin: 5px 0; font-size: 17px;"> {formatted_date}</p>
                <p style="margin: 5px 0; font-size: 17px;"> {game.league.name}</p>
                <p style="margin: 5px 0; font-size: 17px;"> {game.away_team.organization.first_name} vs {game.home_team.organization.first_name}</p>
                <p style="margin: 5px 0; font-size: 17px; font-weight: bold; "> {team_to_bet} ({ml})</p>
                <p style="margin: 5px 0; font-size: 17px; font-weight: bold;">${wager:.2f}</p>
                <p style="margin: 5px 0; font-size: 17px;"><strong>Probability:</strong> {(edge_value + implied_prob):.2f}%</p>
            </div>
            """
        )

    html_lines.append(
        f"""
        <p style="font-size: 16px; margin-top: 20px;">
            Visit our site for more details:
            <a href="https://FEFelson.com{reverse('game_list')}" style="color: #3498db; text-decoration: none; font-weight: bold;">
                FEFelson.com
            </a>
        </p>
        <p style="font-size: 12px; color: #7f8c8d; text-align: center; margin-top: 20px;">
            &copy; {game.game_date.strftime('%Y')} Fast Eddy Felson. All rights reserved.
        </p>
        </body>
        </html>
        """
    )
    body_lines.append(f"\nVisit our site for more details: https://FEFelson.com{reverse('game_list')}\n")

    text_content = "\n".join(body_lines)
    html_content = "".join(html_lines)

    try:
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        return True
    except Exception as e:
        print(f"Failed to send email to {user.email}: {e}")
        return False
