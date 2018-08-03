import i18n from 'i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

i18n
    .use(LanguageDetector)
    .init({
        // we init with resources
        resources: {
            en: {
                translations: {
                    // App.js
                    "error_noRequestID": "Error : this request is invalid. <br/>Please try again to get a valid link by texting COMPASSION to 959. Thank you!",
                    "error_noService": "Error : the service is not available at this time. <br/>Please try again in a few minutes. Thank you!",
                    "error_sponsorshipAlreadyMade": "You already sponsored this child, thank you! <br/><br/> If you want to sponsor another child, please text again COMPASSION to 959.",
                    "waitingForChild": "we are looking for a child waiting for a sponsor, please wait a few seconds...",
                    "waitingForOtherChild": "we are looking for a child matching your request, please wait a few seconds...",
                    "ageYears": " years",
                    // ChildCard.js
                    "cardTitle": "Sponsor a child",
                    "age": "Age",
                    "gender": "Gender",
                    "country": "Country",
                    "Male": "Male",
                    "Female": "Female",
                    // ChildDetails.js
                    "more": "More details",
                    // SponsorForm.js
                    "coordinates": "Your coordinates",
                    "firstname": "Firstname",
                    "lastname": "Lastname",
                    "email": "Email",
                    "sponsorshipPlus": "Sponsorship plus",
                    "otherChild": "Other child",
                    "sponsorNow": "Sponsor now",
                    // ModalForm.js
                    "chooseTitle": "Choose another child",
                    "modalHelp": "Select filters for another child. You can leave the filters empty if you don't want to choose on given criteria.",
                    "genderSelect": "Boy/Girl",
                    "ageSelect": "Age",
                    "countrySelect": "Country",
                    "cancel": "Cancel",
                    "boy": "Boy",
                    "girl": "Girl",
                    "ageCat1": "0-3 years",
                    "ageCat2": "4-6 years",
                    "ageCat3": "7-10 years",
                    "ageCat4": "11-14 years",
                    "ageCat5": "15-20 years",
                    // SponsorshipPlusTabs.js
                    "basicTab": "Sponsorship basic",
                    "basicTitle": "CHF 42.- / month",
                    "basicDescription": "Your monthly support provides life-changing opportunities such as " +
                        "an opportunity to attend or stay in school, " +
                        "medical care, nourishing food, mentoring, and a safe environment. <br/><br/>" +
                        "Compassion child sponsorship works! Millions of children have “graduated” from our program " +
                        "and are now responsible, fulfilled adults.",
                    "plusTab": "Sponsorship plus",
                    "plusTitle": "CHF 50.- / month",
                    "plusDescription": "Sponsorship Plus is the basic sponsorship " +
                        "plus an additional donation of CHF 8.00 per month: <br/><br/>it enables Compassion to finance " +
                        "projects to change the children's environment. " +
                        "The funds received under the Sponsorship Plus program contribute to a common fund " +
                        "and enable Compassion to support several projects each year.",
                    // SuccessMessage.js
                    "successMessage1": "Hooray! {{preferred_name}} will soon receive the good news that you are his sponsor.",
                    "successMessage2": "There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                }
            },
            fr: {
                translations: {
                    // App.js
                    "error_noRequestID": "Erreur : requête invalide. <br/>Pour recevoir un nouveau lien valide, merci d'envoyer COMPASSION par SMS au 959.",
                    "error_noService": "Erreur : le service n'est pas disponible pour le moment. <br/>Veuillez essayer dans quelques minutes. Merci !",
                    "error_sponsorshipAlreadyMade": "Cet enfant est déjà parrainé! <br/><br/> Si vous souhaitez parrainer un autre enfant, merci d'envoyer COMPASSION par SMS au 959.",
                    "waitingForChild": "Merci de patienter quelques secondes pendant que nous recherchons un enfant sans parrain...",
                    "waitingForOtherChild": "Nous recherchons un enfant qui correspond à vos critères, merci de patienter quelques secondes...",
                    "ageYears": " ans",
                    // ChildCard.js
                    "cardTitle": "Parraine un enfant",
                    "age": "Age",
                    "gender": "Sexe",
                    "country": "Pays",
                    "Male": "Garçon",
                    "Female": "Fille",
                    // ChildDetails.js
                    "more": "Plus d'informations",
                    // SponsorForm.js
                    "coordinates": "Vos coordonnées",
                    "firstname": "Prénom",
                    "lastname": "Nom",
                    "email": "Email",
                    "sponsorshipPlus": "Parrainage plus",
                    "otherChild": "Choisir un autre enfant",
                    "sponsorNow": "Parrainer {{name}}",
                    // ModalForm.js
                    "chooseTitle": "Choisir un autre enfant",
                    "modalHelp": "Vous pouvez spécifier ici quelques critères de recherche. Laissez-les simplement vides si vous ne voulez pas choisir.",
                    "genderSelect": "Garçon/Fille",
                    "ageSelect": "Tranche d'âge",
                    "countrySelect": "Pays",
                    "cancel": "Annuler",
                    "boy": "Garçon",
                    "girl": "Fille",
                    "ageCat1": "0-3 ans",
                    "ageCat2": "4-6 ans",
                    "ageCat3": "7-10 ans",
                    "ageCat4": "11-14 ans",
                    "ageCat5": "15-20 ans",
                    // SponsorshipPlusTabs.js
                    "basicTab": "Parrainage standard",
                    "basicTitle": "CHF 42.- / mois",
                    "basicDescription": "Votre soutien mensuel offre des opportunités qui changent la vie telles qu'"+
                         "une opportunité d'assister ou de rester à l'école, " +
                        "des soins médicaux, des repas nourrissants, du mentorat et un environnement sûr. <br/><br/>" +
                        "Le parrainage d'enfants de Compassion fonctionne! Des millions d'enfants ont été diplômés de notre programme " +
                        "et sont maintenant des adultes responsables et accomplis.",
                    "plusTab": "Parrainage plus",
                    "plusTitle": "CHF 50.- / mois",
                    "plusDescription": "Le Sponsorship Plus représente le parrainage basique" +
                        "plus un don additionnel de 8 CHF par mois: <br/><br/>cela permet à Compassion de financer " +
                        "des projets pour changer l'environnement des enfants." +
                        "Les fonds reçus par le Sponsorship Plus contribuent à un fond commun" +
                        "et permettent à Compassion de soutenir plusieurs projets par année.",
                    // SuccessMessage.js
                    "successMessage1": "Félicitations ! {{preferred_name}} sera heureux d'apprendre que vous êtes son parrain.",
                    "successMessage2": "Il reste quelques petites étapes avant de pouvoir débuter le parrainage, mais soyez tranquille : vous recevrez tous les détails nécessaires par e-mail. Vous pourrez ainsi compléter les informations manquantes lorsque vous aurez du temps.",
                }
            },
            de: {
                translations: {
                    // App.js
                    "successMessage_male": "Hurra! {{preferred_name}} wird bald die gute Nachricht erhalten, dass Sie sein Sponsor sind. <br/><br/>Es sind noch ein paar Schritte nötig, um das Sponsoring zu bestätigen, aber keine Sorge: Sie werden alle Details per E-Mail erhalten, damit Sie Ihre Registrierung abschließen können, wenn Sie Zeit haben.",
                    "successMessage_female": "Hooray! {{preferred_name}} wird bald die gute Nachricht erhalten, dass Sie sein Sponsor sind. <br/><br/> Es sind noch ein paar Schritte nötig, um das Sponsoring zu bestätigen, aber keine Sorge: Sie werden alle Details per E-Mail erhalten, damit Sie Ihre Registrierung abschließen können, wenn Sie Zeit haben.",
                    "error_noRequestID": "Fehler: Diese Anfrage ist ungültig. <br/>Bitte versuchen Sie es erneut, um einen gültigen Link zu erhalten, indem Sie COMPASSION an 959 senden. Danke!",
                    "error_sponsorshipAlreadyMade": "Du hast dieses Kind bereits gesponsert, danke! <br/><br/> Wenn Sie ein anderes Kind sponsern möchten, geben Sie bitte erneut COMPASSION bis 959 ein.",
                    "error_noService": "Error : Der Dienst ist zu diesem Zeitpunkt nicht verfügbar. <br/>Bitte versuchen Sie es in ein paar Minuten noch einmal. Vielen Dank!",
                    "waitingForChild": "Wir suchen ein Kind, das auf einen Sponsor wartet, bitte warten Sie ein paar Sekunden ...",
                    "waitingForOtherChild": "Wir suchen ein Kind, das Ihrer Anfrage entspricht, bitte warten Sie ein paar Sekunden ...",
                    "ageYears": " Jahre",
                    // ChildCard.js
                    "cardTitle": "Patenschaft für ein Kind",
                    "age": "Alter",
                    "gender": "Geschlecht",
                    "country": "Land",
                    "Male": "Männlich",
                    "Female": "Weiblich",
                    // ChildDetails.js
                    "more": "Mehr Details",
                    // SponsorForm.js
                    "coordinates": "Ihre Koordinaten",
                    "firstname": "Vorname",
                    "lastname": "Nachname",
                    "email": "Email",
                    "sponsorshipPlus": "Sponsorship plus",
                    "otherChild": "Anderes Kind",
                    "sponsorNow": "Sponsor jetzt",
                    // ModalForm.js
                    "chooseTitle": "Wähle ein anderes Kind",
                    "modalHelp": "Wählen Sie Filter für ein anderes Kind aus. Sie können die Filter leer lassen, wenn Sie nicht nach bestimmten Kriterien auswählen möchten.",
                    "genderSelect": "Wähle einen Jungen oder ein Mädchen",
                    "ageSelect": "Wählen Sie das Alter aus",
                    "countrySelect": "Wähle ein Land",
                    "cancel": "Abbestellen",
                    "boy": "Junge",
                    "girl": "Mädchen",
                    "ageCat1": "0-3 Jahre",
                    "ageCat2": "4-6 Jahre",
                    "ageCat3": "7-10 Jahre",
                    "ageCat4": "11-14 Jahre",
                    "ageCat5": "15-20 Jahre",
                    // SponsorshipPlusTabs.js
                    "basicTab": "Sponsorship basic",
                    "basicTitle": "CHF 42.- / Monat",
                    "basicDescription": "Ihre monatliche Unterstützung bietet lebensverändernde Möglichkeiten wie " +
                        "die Möglichkeit, in der Schule zu bleiben oder zu bleiben, " +
                        "Nahrung zu nähren, Mentoring und eine sichere Umgebung. <br/><br/>" +
                        "Mitgefühlskindersponsoring funktioniert! Millionen von Kindern haben unser Programm absolviert " +
                        "und sind nun verantwortliche, erfüllte Erwachsene.",
                    "plusTab": "Sponsorship plus",
                    "plusTitle": "CHF 50.- / Monat",
                    "plusDescription": "Sponsorship Plus ist die Grundförderung " +
                        "plus eine zusätzliche Spende von CHF 8.00 pro Monat: <br/><br/>Es ermöglicht Compassion, Projekte zu finanzieren, " +
                        "um die Umwelt der Kinder zu verändern. " +
                        "Die im Rahmen des Programms Sponsorship Plus erhaltenen Mittel tragen zu einem gemeinsamen Fonds bei " +
                        "und ermöglichen es Compassion, jedes Jahr mehrere Projekte zu unterstützen."
                }
            },
            it: {
                translations: {
                    // App.js
                    "successMessage_male": "Hooray! {{preferred_name}} will soon receive the good news that you are his sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "successMessage_female": "Hooray! {{preferred_name}} will soon receive the good news that you are her sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "error_noRequestID": "Error : this request is invalid. <br/>Please try again to get a valid link by texting COMPASSION to 959. Thank you!",
                    "error_sponsorshipAlreadyMade": "You already sponsored this child, thank you! <br/><br/> If you want to sponsor another child, please text again COMPASSION to 959.",
                    "error_noService": "Error : the service is not available at this time. <br/>Please try again in a few minutes. Thank you!",
                    "waitingForChild": "we are looking for a child waiting for a sponsor, please wait a few seconds...",
                    "waitingForOtherChild": "we are looking for a child matching your request, please wait a few seconds...",
                    "ageYears": " years",
                    // ChildCard.js
                    "cardTitle": "Sponsor a child",
                    "age": "Age",
                    "gender": "Gender",
                    "country": "Country",
                    "Male": "Male",
                    "Female": "Female",
                    // ChildDetails.js
                    "more": "More details",
                    // SponsorForm.js
                    "coordinates": "Your coordinates",
                    "firstname": "Firstname",
                    "lastname": "Lastname",
                    "email": "Email",
                    "sponsorshipPlus": "Sponsorship plus",
                    "otherChild": "Other child",
                    "sponsorNow": "Sponsor now",
                    // ModalForm.js
                    "chooseTitle": "Choose another child",
                    "modalHelp": "Select filters for another child. You can leave the filters empty if you don't want to choose on given criteria.",
                    "genderSelect": "Choose a boy or a girl",
                    "ageSelect": "Select age",
                    "countrySelect": "Choose a country",
                    "cancel": "Cancel",
                    "boy": "Boy",
                    "girl": "Girl",
                    "ageCat1": "0-3 years",
                    "ageCat2": "4-6 years",
                    "ageCat3": "7-10 years",
                    "ageCat4": "11-14 years",
                    "ageCat5": "15-20 years",
                    // SponsorshipPlusTabs.js
                    "basicTab": "Sponsorship basic",
                    "basicTitle": "CHF 42.- / month",
                    "basicDescription": "Your monthly support provides life-changing opportunities such as " +
                        "an opportunity to attend or stay in school, " +
                        "medical care, nourishing food, mentoring, and a safe environment. <br/><br/>" +
                        "Compassion child sponsorship works! Millions of children have “graduated” from our program " +
                        "and are now responsible, fulfilled adults.",
                    "plusTab": "Sponsorship plus",
                    "plusTitle": "CHF 50.- / month",
                    "plusDescription": "Sponsorship Plus is the basic sponsorship " +
                        "plus an additional donation of CHF 8.00 per month: <br/><br/>it enables Compassion to finance " +
                        "projects to change the children's environment. " +
                        "The funds received under the Sponsorship Plus program contribute to a common fund " +
                        "and enable Compassion to support several projects each year."
                }
            },
        },
        fallbackLng: 'en',
        debug: true,

        // have a common namespace used around the full app
        ns: ['translations'],
        defaultNS: 'translations',

        keySeparator: false, // we use content as keys

        interpolation: {
            escapeValue: false, // not needed for react!!
            formatSeparator: ','
        },

        react: {
            wait: true
        }
    });

export default i18n;