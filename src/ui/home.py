"""A quiet, warm cafeteria table; only implemented routes are advertised."""

def welcome(screen):
    if screen.decor:
        for line in ('       ( (             ( (', '     .-----.         .-----.',
                     '     \\_____/         \\_____/', '   ---------------------------'):
            screen.say(line, 'accent')
    screen.say('Plate Memory  |  Saved you a seat.', 'title')
    screen.paragraph('That bro who ate with you every day back in high school.')
    screen.paragraph('Different campuses. Still a place for you at the table.')


def home(screen, profile, meal_date, synthetic):
    screen.say('\n' + (profile['friend'] if profile else 'Your table') + ' | ' + meal_date.isoformat(), 'title')
    if synthetic:
        screen.say('Synthetic demo: sample places, prices and preferences; changes stay in this session.', 'warn')
    screen.say('1  today        Let’s find you something to eat\n2  lunchbox     Open a little note from your friend\n3  checkin      Already ate? How did it feel?\n4  postcard     Until our next meal\nusuals          Your saved places and dishes')
    screen.paragraph('More: review (check ingredients) / preferences (dietary notes) / date / details / demo / quit')
