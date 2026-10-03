"""A seat saved across campuses; four equal destinations, optional extras."""

def welcome(screen):
    if screen.decor:
        screen.say('  🥣     🥣\n  ─────────────\n  a seat saved for you', 'accent')
    screen.say('Plate Memory  |  Saved you a seat.', 'title')
    screen.paragraph('That bro who ate with you every day back in high school.')
    screen.paragraph('Different campuses. Still a place for you at the table.')


def home(screen, profile, meal_date, synthetic):
    screen.say('\nYour table | '+meal_date.isoformat(), 'title')
    if synthetic:
        screen.say('Synthetic demo. Changes stay in this session.', 'warn')
    labels=[('1','🍽️','Find something to eat'),('2','🎒','A note from your friend'),
            ('3','📝','Already ate? How was it?'),('4','💌','Until our next meal'),
            ('5','📍','Your saved places')]
    for number,icon,label in labels:
        screen.say(number+'  '+(icon+'  ' if screen.decor else '')+label)
    screen.say('6  More options   ·   0  Close')
