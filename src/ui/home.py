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
    screen.say('1  today        Takeout or a walk to the cafeteria\n2  lunchbox     A little note from your friend\n3  checkin      How did that meal feel?\n4  postcard     Until our next meal\nusuals          Your saved places and dishes')
    screen.say('review  Check a menu     preferences  Your dietary notes\ndate    Meal date        details      Last rule trace\ndemo    Menu example     quit         See you next time')
