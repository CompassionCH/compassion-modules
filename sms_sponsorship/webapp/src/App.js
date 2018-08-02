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
    };

    parseResult = (res) => {
        let child;
        try {
            child = JSON.parse(res.responseText).result[0]
        }
        catch(e) {
            child = false;
        }
        return child;
    };

    getChild = () => {
        let lang = i18n.languages[1];
        let requestId = getRequestId();
        if (!requestId) {
            return;
        }
        let url = "/sms_sponsorship/step1/" + requestId + "/get_child_data";
        jsonRPC(url, {lang: lang}, (res) => {
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
        let lang = i18n.languages[1];
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
            }
        });

        jsonRPC(url, data, (res) => {
            this.getChild();
        });
    };

    componentDidMount() {
        if (!window.pageLoaded) {
            window.pageLoaded = true;
            this.getChild();
        }
    }

    render() {
        const { t } = this.props;
        let image_url = '';
        let child = this.state.child;
        if (child && child.image_url) {
            image_url = child.image_url.replace('/w_150', '').replace('media.ci.org/', 'media.ci.org/g_face,c_thumb,w_150,h_150,r_max/');
        }
        let topAppBar = <TopAppBar title="Compassion"/>;

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

        if (!child.has_a_child && !this.state.success) {
            clearTimeout(window.getChildTimeout);
            window.getChildTimeout = setTimeout(() => {
                this.getChild();
            }, 1000);
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