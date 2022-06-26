import asyncio
import json
import logging
from time import gmtime, strftime

from telethon import Button, TelegramClient, events
from telethon.errors import AlreadyInConversationError

from db import Databases
from credential import ADMIN_ID, API_ID, API_HASH, TOKEN



logging.basicConfig(filename="file.log" ,level=logging.DEBUG,
                    format='%(name)s- %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


client = TelegramClient(None, int(API_ID), API_HASH).start(bot_token=TOKEN)  # type: ignore


def get_tip(tips):
    with open("tips.json", "r") as f:
        data = json.load(f)

    return data.get(tips)

async def typing_action(chat_id, chat_action="typing", period=2):
    async with client.action(chat_id, chat_action):  # type: ignore
        await asyncio.sleep(period)


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.respond("Bienvenue sur le bot de gestion de dépense, pour continuer appuyez sur **/options**.")


@client.on(events.NewMessage(pattern="/options"))
async def option(event):
    if event.chat_id != ADMIN_ID:
        return

    keyboard = [
        [Button.inline("REVENUS 💵", b"1"),
         Button.inline("DEPENSES 🛍", b"2")],
         [Button.inline("MODIFIER ✅", b"3"),
         Button.inline("SUPPRIMER 🗑", b"4")],
         [Button.inline("TOTALS 💰", b"5")]
    ]

    await client.send_message(ADMIN_ID, "Choississez une option:", buttons=keyboard)



async def totals(chat_id, event):
    if chat_id != ADMIN_ID:
        return
        
    d = Databases()
    await typing_action(chat_id)

    revenu = "REVENUS:      __{:,} XOF__".format(d.get_income_expense('revenus'))
    depense = "DEPENSES:    __{:,} XOF__".format(d.get_income_expense('depenses'))
    solde = "SOLDE:       __{:,} XOF__".format(d.last_value('balance'))
    
    await event.respond(f"RECAPITULATIF\n\n{revenu}\n{depense}\n{solde}")
    logger.info(f"----> LE TOTAL DES DONNÉS A ÉTÉ DEMANDÉ")



@client.on(events.CallbackQuery())
async def button(event):

    if event.data == b"1":
        await event.delete()
        await user_conversation(chat_id=ADMIN_ID, tips=get_tip("REVENU"), earn=True)

    elif event.data == b"2":
        await event.delete()
        await user_conversation(chat_id=ADMIN_ID, tips=get_tip("DEPENSE"), earn=False)
    
    elif event.data == b"3":
        await event.delete()
        await update_table(chat_id=ADMIN_ID, tips=get_tip("UPDATE"))

    
    elif event.data == b"4":
        pass


    elif event.data == b"5":
        await event.delete()
        await totals(chat_id=ADMIN_ID, event=event)


    raise events.StopPropagation




async def user_conversation(chat_id, tips, earn):

    try:
        async with client.conversation(chat_id, timeout=60) as conv:
            await conv.send_message(tips, parse_mode='md')

            try:
                continue_conv = True

                while continue_conv:
                    response = conv.get_response()
                    response = await response

                    if response.raw_text != "/end":
                        day = strftime("%d-%m-%Y", gmtime())
                        hour = strftime("%H:%M:%S", gmtime())

                        if earn:
                            await typing_action(chat_id)
                            await add_data(conv, day, hour, response, save=True)

                        else:
                            await typing_action(chat_id)
                            await add_data(conv, day, hour, response)

                    else:
                        await conv.send_message(get_tip("END"))
                        continue_conv = False

            except asyncio.TimeoutError:
                await typing_action(chat_id)
                await conv.send_message("Conversation terminée 🔚!\n\nPour afficher les options appuyez sur **/options**.")

    except AlreadyInConversationError:
        await client.send_message(chat_id, "Veuillez terminer la conversation avant de choisir d'autre options.")  # type: ignore




async def add_data(conv, day, hour, response, save=False):
    msg = str(response.raw_text).split()
    amount = msg[0]
    description = " ".join(msg[1:]).upper()
    
    try:
        d = Databases()
        # Forcer l'utilisateur à écrire plus de 3 mots.
        if description.count("") > 3:

            # if save --> True alors l'utilisateur enregistre ses revenus.
            if save:
                balance = int(amount) + d.last_value('balance')
                d.save_data(date=day, hour=hour, income=amount, description=description, balance=balance)

                await conv.send_message(f"Revenu enregistré 📝.")
                logger.info(f"----------> MONTANT AJOUTÉ: {amount} XOF | MOTIF: {description}")
            else:
                balance = d.last_value('balance') - int(amount)
                d.save_data(date=day, hour=hour, expense=amount, description=description, balance=balance)

                await conv.send_message("Votre dépense a été enregistré 📝.")
                logger.info(f"----------> MONTANT DEPENSÉ: {amount} XOF | MOTIF: {description}")

        else:
            await conv.send_message(get_tip("FORMAT"))
            logger.info(f"---> LA VALEUR ENTRÉ NE CORRESPOND PAS AVEC LE FORMAT DONNÉ.")
    except ValueError:
        await conv.send_message(get_tip("FORMAT"))
        logger.info(f"---> LA VALEUR ENTRÉ NE CORRESPOND PAS AVEC LE FORMAT DONNÉ.")



async def update_table(chat_id, tips):
    if chat_id != ADMIN_ID:
        return
    
    try:
        async with client.conversation(chat_id, timeout=125) as conv:
            await conv.send_message(tips, parse_mode='md')

            try:
                continue_conv = True

                while continue_conv:
                    response = conv.get_response()
                    response = await response

                    if response.raw_text != "/end":
                        d = Databases()
                        column = d.column
                        answer = response.raw_text.split()
                        
                        try:
                            # Get all colums index to update 
                            find_index = [answer.index(w) for w in answer if w.lower() in column]
                            
                            # Get the text of the value to be updated
                            row = answer[find_index[0]]
                            new_value = " ".join(answer[find_index[0]+1: find_index[1]])
                            row_index = answer[find_index[1]]
                            row_value = " ".join(answer[find_index[1]+1:])

                            # Convert users input to match table colums in database
                            d.update_value(row=row.lower(), new_value=new_value, row_index=row_index.lower(), row_value=row_value)

                            await typing_action(chat_id, period=1)
                            await conv.send_message("Modification effectué avec succès...")

                            logger.info(f"----------> MODIFICATION: {row.lower()} *** {new_value} *** {row_index.lower()} *** {row_value} *** .")

                        except IndexError:
                            column = " - ".join(column)
                            await conv.send_message(f"Veuillez suivre le format correct et verifiez l'orthographe des colonnes. Voici la liste des colonnes:\n\n{column}")

                            logger.info(f"---> LA VALEUR ENTRÉ NE CORRESPOND PAS AVEC LE FORMAT DONNÉ.")

                    else:
                        await conv.send_message(get_tip("END"))
                        continue_conv = False

            except asyncio.TimeoutError:
                await conv.send_message("Conversation terminée 🔚!\n\nPour afficher les options appuyez sur **/options**.")


    except AlreadyInConversationError:
        await client.send_message(chat_id, "Veuillez terminer la conversation avant de choisir d'autre options.")  # type: ignore







if __name__ == "__main__":
    print("\n\nBOT EN COURS ....\n\n")
    client.run_until_disconnected()
