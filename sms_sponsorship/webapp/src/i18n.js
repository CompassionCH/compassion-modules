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
                    "successMessage_male": "Hooray! {{preferred_name}} will soon receive the good news that you are his sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "successMessage_female": "Hooray! {{preferred_name}} will soon receive the good news that you are her sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "error_noRequestID": "Error : this request is invalid. <br/>Please try again to get a valid link by texting COMPASSION to 959. Thank you!",
                    "error_sponsorshipAlreadyMade": "You already sponsored this child, thank you! <br/><br/> If you want to sponsor another child, please text again COMPASSION to 959.",
                    "waitingForChild": "we are looking for a child waiting for a sponsor, please wait a few seconds...",
                    "waitingForOtherChild": "we are looking for a child matching your request, please wait a few seconds...",
                    "ageYears": " years",
                    // ChildCard.js
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
                }
            },
            fr: {
                translations: {
                    // App.js
                    "successMessage_male": "Félicitations ! {{preferred_name}} sera heureux d'apprendre que vous le parrainez. <br/><br/>Il reste quelques petite étapes avant de pouvoir débuter le parrainage, mais soyez tranquille : vous recevrez tous les détails nécessaires par e-mail. Vous pourrez ainsi compléter les informations manquantes lorsque vous aurez du temps.",
                    "successMessage_female": "Félicitations ! {{preferred_name}} sera heureux d'apprendre que vous la parrainez. <br/><br/>Il reste quelques petite étapes avant de pouvoir débuter le parrainage, mais soyez tranquille : vous recevrez tous les détails nécessaires par e-mail. Vous pourrez ainsi compléter les informations manquantes lorsque vous aurez du temps.",
                    "error_noRequestID": "Erreur : requête invalide. <br/>Pour recevoir un nouveau lien valide, merci d'envoyer COMPASSION par SMS au 959.",
                    "error_sponsorshipAlreadyMade": "Cet enfant est déjà parrainé! <br/><br/> Si vous souhaitez parrainer un autre enfant, merci d'envoyer COMPASSION par SMS au 959.",
                    "waitingForChild": "Merci de patienter quelques secondes pendant que nous recherchons un enfant sans parrain...",
                    "waitingForOtherChild": "Nous recherchons un enfant qui correspond à tes critères, merci de patienter quelques secondes...",
                    "ageYears": " ans",
                    // ChildCard.js
                    "age": "Age",
                    "gender": "Sexe",
                    "country": "Pays",
                    "Male": "Garçon",
                    "Female": "Fille",
                    // ChildDetails.js
                    "more": "Plus d'informations",
                    // SponsorForm.js
                    "coordinates": "Tes coordonnées",
                    "firstname": "Prénom",
                    "lastname": "Nom",
                    "email": "Email",
                    "sponsorshipPlus": "Parrainage plus",
                    "otherChild": "Autre enfant",
                    "sponsorNow": "Parrainer maintenant",
                    // ModalForm.js
                    "chooseTitle": "Choisir un autre enfant",
                    "modalHelp": "Tu peux spécifier ici quelques critères de recherche. Laisse-les simplement vides si tu ne veux pas choisir.",
                    "genderSelect": "Choisis un garçon ou une fille",
                    "ageSelect": "Choisis une tranche d'âge",
                    "countrySelect": "Choisis un pays",
                    "cancel": "Annuler",
                    "boy": "Garçon",
                    "girl": "Fille",
                    "ageCat1": "0-3 ans",
                    "ageCat2": "4-6 ans",
                    "ageCat3": "7-10 ans",
                    "ageCat4": "11-14 ans",
                    "ageCat5": "15-20 ans",
                }
            },
            de: {
                translations: {
                    // App.js
                    "successMessage_male": "Hooray! {{preferred_name}} will soon receive the good news that you are his sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "successMessage_female": "Hooray! {{preferred_name}} will soon receive the good news that you are her sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "error_noRequestID": "Error : this request is invalid. <br/>Please try again to get a valid link by texting COMPASSION to 959. Thank you!",
                    "error_sponsorshipAlreadyMade": "You already sponsored this child, thank you! <br/><br/> If you want to sponsor another child, please text again COMPASSION to 959.",
                    "waitingForChild": "we are looking for a child waiting for a sponsor, please wait a few seconds...",
                    "waitingForOtherChild": "we are looking for a child matching your request, please wait a few seconds...",
                    "ageYears": " years",
                    // ChildCard.js
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
                }
            },
            it: {
                translations: {
                    // App.js
                    "successMessage_male": "Hooray! {{preferred_name}} will soon receive the good news that you are his sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "successMessage_female": "Hooray! {{preferred_name}} will soon receive the good news that you are her sponsor. <br/><br/>There a few more steps required to confirm the sponsorship, but no worries: you will receive all the details per e-mail so that you can complete your registration when you have time.",
                    "error_noRequestID": "Error : this request is invalid. <br/>Please try again to get a valid link by texting COMPASSION to 959. Thank you!",
                    "error_sponsorshipAlreadyMade": "You already sponsored this child, thank you! <br/><br/> If you want to sponsor another child, please text again COMPASSION to 959.",
                    "waitingForChild": "we are looking for a child waiting for a sponsor, please wait a few seconds...",
                    "waitingForOtherChild": "we are looking for a child matching your request, please wait a few seconds...",
                    "ageYears": " years",
                    // ChildCard.js
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