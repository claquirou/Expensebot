import asyncio
import json
import logging
from time import gmtime, strftime

from telethon import Button, TelegramClient, events
from telethon.errors import AlreadyInConversationError

import init_db
from db import Databases, last_month
from credential import ADMIN_ID, API_ID, API_HASH, TOKEN

logging.basicConfig(filename="file.log", level=logging.DEBUG,
                    format='%(name)s- %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = TelegramClient(None, int(API_ID), API_HASH).start(bot_token=TOKEN)  # type: ignore

MONTH = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre",
         "decembre"]


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
    keyboard = [
        [Button.inline("REVENUS 💵", b"1"),
         Button.inline("DEPENSES 🛍", b"2")],
        [Button.inline("MODIFIER ✅", b"3"),
         Button.inline("SUPPRIMER 🗑", b"4")],
        [Button.inline("TOTALS 💰", b"5")]
    ]

    await client.send_message(ADMIN_ID, "Choississez une option:", buttons=keyboard)


@client.on(events.NewMessage(pattern="/month"))
async def new_month(event):
    keyboard = [
        [Button.inline("MOIS ACTUEL", b"6"),
         Button.inline("NOUVEAU MOIS", b"7")]
    ]

    await client.send_message(ADMIN_ID, "Choississez une option:", buttons=keyboard)


@client.on(events.CallbackQuery())
async def _option_button(event):
    if event.data == b"1":
        await event.delete()
        await _user_conversation(chat_id=ADMIN_ID, tips=get_tip("REVENU"), arg="income")

    elif event.data == b"2":
        await event.delete()
        await _user_conversation(chat_id=ADMIN_ID, tips=get_tip("DEPENSE"), arg="expense")

    elif event.data == b"3":
        await event.delete()
        await _user_conversation(chat_id=ADMIN_ID, tips=get_tip("UPDATE"), arg="update")

    elif event.data == b"4":
        await event.delete()
        await _user_conversation(chat_id=ADMIN_ID, tips=get_tip("DELETE"), arg="delete")

    elif event.data == b"5":
        await event.delete()
        await get_totals(chat_id=ADMIN_ID, event=event)

    if event.data == b"6":
        # await event.delete()
        # await _user_conversation(chat_id=event.chat_id, tips="Ecrivez le nom du mois dont vous souhaitez avoir les donnés.", arg="setMonth")
        pass

    elif event.data == b"7":
        await event.delete()
        await _user_conversation(chat_id=event.chat_id, tips="Ecrivez le nom du nouveau mois.", arg="addMonth")

    raise events.StopPropagation


async def _user_conversation(chat_id: int, tips: str, arg: str):
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

                        if arg == "addMonth":
                            await add_new_month(chat_id=chat_id, response=response, conv=conv)
                            return

                        elif arg == "setMonth":
                            pass

                        elif arg == "income":
                            await typing_action(chat_id)
                            await add_data(conv=conv, day=day, hour=hour, response=response, save=True)

                        elif arg == "update":
                            await typing_action(chat_id, period=1)
                            await update_table(response=response, conv=conv, delete=False)

                        elif arg == "delete":
                            await typing_action(chat_id, period=1)
                            await update_table(response=response, conv=conv, delete=True)

                        else:
                            await typing_action(chat_id)
                            await add_data(conv=conv, day=day, hour=hour, response=response, save=False)

                    else:
                        await conv.send_message(get_tip("END"))
                        continue_conv = False

            except asyncio.TimeoutError:
                await typing_action(chat_id)
                await conv.send_message(get_tip("TIMEOUT_ERROR"))

    except AlreadyInConversationError:
        await client.send_message(chat_id, get_tip("CONVERSATION_ERROR"))  # type: ignore


async def get_totals(chat_id, event):
    d = Databases()
    
    try :
        await typing_action(chat_id)
        revenu = "REVENUS:      __{:,} XOF__".format(d.get_income_expense('revenus'))
        depense = "DEPENSES:    __{:,} XOF__".format(d.get_income_expense('depenses'))
        solde = "SOLDE:       __{:,} XOF__".format(d.last_value('balance'))

        await event.respond(f"RECAPITULATIF DU MOIS __{last_month().upper()}__\n\n{revenu}\n{depense}\n{solde}")
        logger.info(f"----> LE TOTAL DES DONNÉS A ÉTÉ DEMANDÉ ET VALEUR = 0 EST SUPPRIMEE")

    except IndexError:
        await event.respond(f"Aucune donnée n'a été enregistré pour le mois {last_month()}")

async def add_data(conv, day, hour, response, save: bool):
    msg = str(response.raw_text).split()
    amount = msg[0]
    description = " ".join(msg[1:]).upper()

    try:
        d = Databases()
        # Forcer l'utilisateur à écrire plus de 3 mots.
        if description.count("") > 3:
            
            try:
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
            
            except IndexError:
                if save:
                    d.save_data(date=day, hour=hour, income=amount, description=description, balance=int(amount))
                    
                    await conv.send_message(f"Revenu enregistré 📝.")
                    logger.info(f"----------> MONTANT AJOUTÉ: {amount} XOF | MOTIF: {description}")
                else:
                    await conv.send_message(f"Vous devez ajouter un revenu avant d'ajouter des dépenses.{get_tip('OPTION_MSG')}")
                    return

        else:
            await conv.send_message(get_tip("FORMAT"))
            logger.info(f"---> {get_tip('FORMAT_ERROR')}")
    except ValueError:
        await conv.send_message(get_tip("FORMAT"))
        logger.info(f"---> {get_tip('FORMAT_ERROR')}")


async def update_table(response, conv, delete: bool):
    d = Databases()
    column = d.column
    answer = response.raw_text.split()

    try:
        if delete:
            row = answer[0]
            value = " ".join(answer[1:])

            try:
                # Convert users input to match table columns in database and delete
                d.delete_value(row=row.lower(), value=value)
                await conv.send_message("Suppression effectué avec succès...")
                logger.info(f"----------> SUPPRESSION: {row.lower()}  *** {value} *** .")

            except ValueError:
                await conv.send_message("Pour modifier une valeur, vous devez forcement passer par la description\nVeuillez suivre l'exemple....")

        else:
            # Get all columns index to update
            find_index = [answer.index(w) for w in answer if w.lower() in column]

            # Get the text of the value to be updated
            row = answer[find_index[0]]
            new_value = " ".join(answer[find_index[0] + 1: find_index[1]])
            row_index = answer[find_index[1]]
            row_value = " ".join(answer[find_index[1] + 1:])

            # Convert users input to match table columns in database and update
            d.update_value(row=row.lower(), new_value=new_value, row_index=row_index.lower(),
                           row_value=row_value)

            await conv.send_message("Modification effectué avec succès...")
            logger.info(f"----------> MODIFICATION: {row.lower()} *** {new_value} *** {row_index.lower()} *** {row_value} *** .")

    except IndexError:
        column = " - ".join(column)
        await conv.send_message(f"{get_tip('INDEX_ERROR')}:\n\n{column}")

        logger.info(f"---> {get_tip('FORMAT_ERROR')}")


async def add_new_month(chat_id, response, conv):
    d = Databases()
    user_entry = str(response.raw_text)

    if user_entry.lower() in MONTH:
        init_db.add_month(user_entry.lower())
        # Supprimer la valeur 0 qui à été initialisé.
        d.delete_value("heure", "0")
        await typing_action(chat_id)
        await conv.send_message(f"{get_tip('NEW_MONTH')} __{user_entry.upper()}__. {get_tip('OPTION_MSG')}")
        logger.info(f"-----> NOUVEAU MOIS AJOUTÉ: {user_entry.upper()}")

    else:
        await typing_action(chat_id)
        await conv.send_message("Ecrivez le nom du mois correct svp...")


async def set_month():
    pass


if __name__ == "__main__":
    print("\n\nBOT EN COURS ....\n\n")
    client.run_until_disconnected()
