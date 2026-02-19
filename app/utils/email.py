"""
Service d'email simulé : les messages sont écrits dans emails.log
et affichés dans la console. Aucun email réel n'est envoyé.
"""
import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger('email_service')


def _log_email(destinataire: str, sujet: str, corps: str):
    """Écrit l'email simulé dans le fichier de logs et la console."""
    separateur = '─' * 60
    message = (
        f"\n{separateur}\n"
        f"[EMAIL SIMULÉ - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}]\n"
        f"Destinataire : {destinataire}\n"
        f"Sujet        : {sujet}\n"
        f"Corps        :\n{corps}\n"
        f"{separateur}\n"
    )
    print(message)
    try:
        log_file = current_app.config.get('MAIL_LOG_FILE', 'emails.log')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(message)
    except Exception:
        pass


def envoyer_bienvenue(utilisateur):
    corps = (
        f"Bonjour {utilisateur.prenom} {utilisateur.nom},\n\n"
        f"Bienvenue chez Vite & Gourmand !\n\n"
        f"Votre compte a bien été créé avec l'adresse e-mail : {utilisateur.email}\n\n"
        f"Vous pouvez dès maintenant consulter nos menus et passer commande.\n\n"
        f"À bientôt,\nL'équipe Vite & Gourmand"
    )
    _log_email(utilisateur.email, "Bienvenue chez Vite & Gourmand !", corps)


def envoyer_reinitialisation(utilisateur, lien: str):
    corps = (
        f"Bonjour {utilisateur.prenom} {utilisateur.nom},\n\n"
        f"Vous avez demandé la réinitialisation de votre mot de passe.\n\n"
        f"Cliquez sur le lien suivant (valable 1 heure) :\n{lien}\n\n"
        f"Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n\n"
        f"L'équipe Vite & Gourmand"
    )
    _log_email(utilisateur.email, "Réinitialisation de votre mot de passe", corps)


def envoyer_confirmation_commande(commande):
    u = commande.utilisateur
    corps = (
        f"Bonjour {u.prenom} {u.nom},\n\n"
        f"Votre commande n°{commande.numero} a bien été enregistrée.\n\n"
        f"Menu    : {commande.menu.titre}\n"
        f"Date    : {commande.date_prestation.strftime('%d/%m/%Y')} à {commande.heure_livraison}\n"
        f"Lieu    : {commande.adresse_livraison}, {commande.ville_livraison}\n"
        f"Personnes : {commande.nb_personnes}\n"
        f"Prix total : {commande.prix_total:.2f} €\n\n"
        f"Nous vous confirmerons votre commande dans les plus brefs délais.\n\n"
        f"L'équipe Vite & Gourmand"
    )
    _log_email(u.email, f"Confirmation de votre commande n°{commande.numero}", corps)


def envoyer_commande_terminee(commande):
    u = commande.utilisateur
    corps = (
        f"Bonjour {u.prenom} {u.nom},\n\n"
        f"Votre commande n°{commande.numero} est désormais terminée.\n\n"
        f"Nous espérons que votre événement s'est bien déroulé !\n\n"
        f"Connectez-vous à votre espace client pour nous laisser votre avis :\n"
        f"http://localhost:5000/utilisateur/commandes\n\n"
        f"Merci de votre confiance,\nL'équipe Vite & Gourmand"
    )
    _log_email(u.email, f"Votre commande n°{commande.numero} est terminée — donnez votre avis !", corps)


def envoyer_retour_materiel(commande):
    u = commande.utilisateur
    corps = (
        f"Bonjour {u.prenom} {u.nom},\n\n"
        f"Nous vous rappelons que du matériel a été prêté lors de votre commande n°{commande.numero}.\n\n"
        f"Conformément aux conditions générales de vente, si le matériel n'est pas restitué "
        f"sous 10 jours ouvrés, des frais de 600 € vous seront facturés.\n\n"
        f"Pour organiser la restitution, contactez-nous par téléphone ou par e-mail.\n\n"
        f"L'équipe Vite & Gourmand"
    )
    _log_email(u.email, "Rappel : restitution du matériel prêté", corps)


def envoyer_compte_employe(employe, mot_de_passe_temp: str = None):
    corps = (
        f"Bonjour {employe.prenom} {employe.nom},\n\n"
        f"Un compte employé Vite & Gourmand a été créé pour vous.\n\n"
        f"Identifiant (e-mail) : {employe.email}\n"
        f"Mot de passe         : [confidentiel – rapprochez-vous de l'administrateur]\n\n"
        f"Connectez-vous sur : http://localhost:5000/auth/connexion\n\n"
        f"L'équipe Vite & Gourmand"
    )
    _log_email(employe.email, "Votre compte employé Vite & Gourmand", corps)


def envoyer_contact(titre: str, description: str, email_expediteur: str):
    corps = (
        f"Nouveau message reçu via le formulaire de contact :\n\n"
        f"De      : {email_expediteur}\n"
        f"Titre   : {titre}\n\n"
        f"Message :\n{description}"
    )
    _log_email("contact@viteetsourmand.fr", f"[Contact] {titre}", corps)
