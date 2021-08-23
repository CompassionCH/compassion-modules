import React from 'react';
import TopAppBar from './components/TopAppBar';
import ChildCard from './components/ChildCard';
import { translate } from 'react-i18next';
import i18n from './i18n';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import CenteredLoading from './components/CenteredLoading';
import jsonRPC from './components/jsonRPC';
import getRequestId from './components/getRequestId';
import Message from './components/Message';
import SuccessMessage from './components/SuccessMessage';
import Button from "@material-ui/core/Button";
import WarningMessage from './components/WarningMessage';

const theme = createMuiTheme({
    palette: {
        primary: {
            main: '#0054A6'
        },
    },
    overrides: {
        // Name of the component ⚛️ / style sheet
        MuiTypography: {
            // Name of the rule
            headline: {
                color: '#555555'
            },
            title: {
                color: '#555555'
            }
        },
        MuiCardHeader: {
            title: {
                textAlign: 'center',
                fontSize: '30px',
                // textTransform: 'uppercase'
            }
        },
        MuiSnackbarContent: {
            root: {
                backgroundColor: "darkred"
            }
        }
    },
});

window.pageLoaded = false;
window.getChildTimeout = false;

class Main extends React.Component {
    state = {
        child: false,
        partner: false,
        success: false,
        langDialog: false,
        langChanged: false,
        dialogOpen: false,
    };

    count_try = 0;

    parseResult = (res) => {
        let child;
        try {
            child = JSON.parse(res.responseText).result
        }
        catch(e) {
            child = false;
        }
        return child;
    };

    getChild = (forceLang) => {
        let data = {};
        if (forceLang || this.state.langChanged) {
            data.lang = i18n.language
        }
        let requestId = getRequestId();
        if (!requestId) {
            return;
        }
        let url = "/sms_sponsorship/step1/" + requestId + "/get_child_data";
        jsonRPC(url, data, (res) => {
            let child = this.parseResult(res);
            let partner = (typeof(child.partner) === 'undefined') ? false:child.partner[0];
            this.setState({
                child: child,
                partner: partner,
            });
        });
    };

    changeChild = () => {
        let requestId = getRequestId();
        let lang = i18n.language;
        let url = "/sms_sponsorship/step1/" + requestId + "/change_child";
        let form = document.forms.other_child_form;

        let data = {
            gender: form.gender.value,
            age: form.age.value,
            country: form.country.value,
            lang: lang,
        };

        this.setState({
            child: {
                'has_a_child': true,
                'loading_other_child': true
            },
            dialogOpen: false
        });

        jsonRPC(url, data, (res) => {
            if (res.response){
                const r = JSON.parse(res.response);
                if (r.result && r.result.code === 416){
                    // Add warning message
                    this.setState({
                        notMatchCriteria: true,
                        child:{
                           'loading_other_child': false
                        }
                    });
                    setTimeout(() => {
                        this.setState({
                            notMatchCriteria: false
                        })
                    }, 5000);
                }
                else{
                    this.getChild();
                }
            }
        });
    };

    changeLanguage = () => {
        let form = document.forms.lang_form;
        let lang = form.lang.value;

        let requestId = getRequestId();
        let url = "/sms_sponsorship/step1/" + requestId + "/change_language";
        let data = {
            lang: lang,
        };
        jsonRPC(url, data);

        i18n.changeLanguage(lang);
        this.setState({
            langDialog: false,
            langChanged: true,
        });
        this.getChild(lang);
    };

    componentDidMount() {
        if (!window.pageLoaded) {
            window.pageLoaded = true;
            this.getChild();
        }
    }

    reload() {
        window.location.reload();
    }

    redirectToWebsite(url) {
        window.location.href = url;
    }

    render() {
        const { t } = this.props;
        document.title = t("cardTitle");
        let image_url = '';
        let child = this.state.child;
        if (child && child.image_url) {
            image_url = child.image_url.replace('/w_150', '').replace('media.ci.org/', 'media.ci.org/g_face,c_thumb,w_150,h_150,r_max/');
        }
        let topAppBar = <TopAppBar title="Compassion" t={t} appContext={this}/>;

        if (!getRequestId()) {
            return (
                <div>
                    {topAppBar}
                    <div>
                        <Message text={t("error_noRequestID")}/>
                    </div>
                </div>
            )
        }

       if (!child.has_a_child && !this.state.success && !child.sponsorship_confirmed && !child.invalid_sms_child_request) {
            clearTimeout(window.getChildTimeout);
            if(this.count_try > 40){
                return (
                            <div>
                                {topAppBar}
                                <Message text={t("error_noService")} style={{marginBottom: '20px'}}/>
                                <div style={{textAlign: 'center', marginTop: '20px'}}>
                                    <Button variant="contained"
                                            onClick={this.reload}
                                            color="primary"
                                            size="medium"
                                    >
                                        {t("error_refresh")}
                                    </Button>
                                    <br/>
                                    <br/>
                                    <Button variant="outlined"
                                            onClick={() => this.redirectToWebsite(t('error_websiteUrl'))}
                                            color="primary"
                                            size="medium"
                                    >
                                        {t("error_sponsorFromWebsite")}
                                    </Button>
                                </div>
                            </div>
                        )
            }else{
                window.getChildTimeout = setTimeout(() => {
                this.getChild();
                }, 1000);
                ++this.count_try;
            }
        }

        return (
            <MuiThemeProvider theme={theme}>
                <div>
                    {topAppBar}
                    {this.state.success ? (
                        <SuccessMessage preferred_name={this.state.success.preferred_name}
                                        gender={this.state.success.gender}
                                        image_url={this.state.success.image_url.replace('/w_150', '').replace('media.ci.org/', 'media.ci.org/g_face,c_thumb,w_150,h_150,r_max/')} t={t}
                        />
                        ):(
                        <div>
                            {child ? (
                                <div>
                                    {child.sponsorship_confirmed ? (
                                        <div>
                                            <Message text={t('error_sponsorshipAlreadyMade')}/>
                                        </div>
                                    ):(
                                        <div>
                                            {!child.invalid_sms_child_request ? (
                                                <div>
                                                    {!child.loading_other_child ? (
                                                        <div>
                                                            {child.has_a_child ? (

                                                                <div>
                                                                {this.state.notMatchCriteria ? (
                                                                <WarningMessage text={t("notMatchCriteria")} />
                                                                ):(<p/>)}

                                                                <ChildCard centered
                                                                           name={child.name}
                                                                           preferredName={child.preferred_name}
                                                                           country={child.country}
                                                                           age={child.age + ' ' + t('ageYears')}
                                                                           gender={child.gender === 'M' ? 'Male':'Female'}
                                                                           image_url={image_url}
                                                                           appContext={this}
                                                                           t={t}
                                                                />
                                                                </div>
                                                            ):(
                                                                <CenteredLoading text={t("waitingForChild")}/>
                                                            )}
                                                        </div>
                                                    ):(
                                                        <div>
                                                            <CenteredLoading text={t("waitingForOtherChild")}/>
                                                        </div>
                                                    )}
                                                </div>
                                            ):(
                                                <div>
                                                    <Message text={t("error_noRequestID")}/>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ):(
                                <div>
                                    <CenteredLoading text={t("waitingForChild")}/>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </MuiThemeProvider>
        )
    }
}

// extended main view with translate hoc
export default translate('translations')(Main);