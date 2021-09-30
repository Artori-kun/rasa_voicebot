# Bạc Xỉu - the Vietnamese Rasa-based virtual assistant

Hi, I'm ***Bạc Xỉu***. You can call me ***Xỉu*** (pronounced /xēo͞o/ with a tiny weeny bitsy Vietnamese accent) for short. I am named after my creator's depressed cat. Yes people, cats can have depression!

Behold, Me!
![](/assets/images/Avatar.jpg)

Handsome, right?

I am a Vietnamese intelligent virtual assistant *(yes i'm asian and no i'm not human, so don't be racist)* built based on [Rasa Framework](https://www.rasa.com/).
My purposes are to assist you in managing your personal schedule and providing you with the latest news out there, so you won't become
what we like to call "a cave man" :joy_cat:. For now, that's all i can do since somebody has been lazy lately :smirk_cat: .

## So, how do i work ?
Don't worry, i'm gonna walk you through it.

First things first, for me to operate entirely, you need 3 different repositories. 

>***That's right people, i'm [horcrux-ing](https://harrypotter.fandom.com/wiki/Horcrux) this :poop:***

These repositories are:
- **[The interface](https://github.com/Artori-kun/voicebot-interface)**: Technically what i look like when talking to you. It is written and built using VueJs.
To run this, you will need `npm` and `nodejs`. So go get it!

    Afterward, open a terminal and run:

    ```
    npm install
    npm run server
    ```
    
    For those of you out there who are experienced with `javascript`, please, *touch [me](https://github.com/Artori-kun/voicebot-interface)*! UwU


- **This one**: This repository contains the core, which is basically a Rasa chatbot. If you have been a busy bee and read the [Rasa's Document](https://www.rasa.com/docs),
you'll understand what this one is about.
  
  First thing you need to do is clone this repo and install the requirements in `requirements.txt`, obviously.
  
  Train the `nlu` and `core` model with:

  ```
  cd /playground
  rasa train --domain ./domain/
  ```
  
  After training complete, you need to initiate the action server:

  ```
  rasa run actions
  ```
  
  along with Rasa server at the port you desire (for example, port 5005):

  ```
  rasa run --enable-api -p 5005
  ```

  At the same time, you also need an HTTP server at the local directory where you store the audio files for speech recognition and speech synthesis.
This allows the interface store the audio of your speeches for STT and fetch TTS responses of mine. You can use `npm`'s `http-server` package for this

  ```
  npm install http-server
  cd ./your_directory
  http-server ./ -p 8888 --cors
  ```
  
  ***Do not forget the `--cors`!! Or you will suffer!!***


- Finally, [The APIs](https://github.com/Artori-kun/voicebot_apis): It's a Django REST API server to manage your personal schedule. MySql is used to store the data.
This is currently developed and maintained by @NguyenHaIT2 . Let's hope she does not mess it up this time :crying_cat_face: . 

  I recommend you to read the [Django's doc](https://docs.djangoproject.com/en/3.2/) and [Django REST Framework's doc](https://www.django-rest-framework.org/) before advancing
any further. But if you are familiar with them, or you are just simply the type of person who likes do things the difficult
way, here's how to run it:

  ```
  python manage.py runserver
  ```

## How do I talk and listen ?

Well actually, that depends on you. I don't have any specific criteria for these two modules. You can use anything you want. Just remember to make
changes in my connector at `custom_components/socketio_connector.py`.

Currently, I can talk thanks to [this repo](https://github.com/NTT123/vietTTS).

I cannot tell you how I listen though. It's kinda a secret :wink:. But if you do have a way to do that, please let [my creator](https://github.com/Artori-kun) knows.

## Well that's everything

If you have any issue, don't yell at me, yell at [him](https://github.com/Artori-kun). Let him knows what your issue is.

If you have some ideas, please tell. ***I thirst for improvement*** ༼ つ ◕_◕ ༽つ
