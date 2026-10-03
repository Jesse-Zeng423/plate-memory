"""A seat saved across campuses; four equal destinations, optional extras."""

def welcome(screen):
    if screen.decor:
        screen.say(screen.t('  🥣     🥣\n  ─────────────\n  a seat saved for you'), 'accent')
    screen.say(screen.t('Plate Memory  |  Saved you a seat.'), 'title')
    screen.paragraph(screen.t('That bro who ate with you every day back in high school.'))
    screen.paragraph(screen.t('Different campuses. Still a place for you at the table.'))


def home(screen, profile, meal_date, synthetic):
    screen.say(screen.t('\nYour table | ')+meal_date.isoformat(), 'title')
    if synthetic:
        screen.say(screen.t('Synthetic demo. Changes stay in this session.'), 'warn')
    labels=[('1','🍽️','Find something to eat'),('2','🎒','A note from your friend'),
            ('3','📝','Already ate? How was it?'),('4','💌','Until our next meal'),
            ('5','📍','Your saved places')]
    for number,icon,label in labels:
        screen.say(number+'  '+(icon+'  ' if screen.decor else '')+screen.t(label))
    screen.say(screen.t('6  More options   ·   0  Close'))
