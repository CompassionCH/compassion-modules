import React from 'react';
import TopAppBar from './components/TopAppBar';
import ChildCard from './components/ChildCard';
import CircularProgress from '@material-ui/core/CircularProgress';
import Typography from '@material-ui/core/Typography';
import { translate } from 'react-i18next';
import i18n from './i18n';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import CenteredLoading from './components/CenteredLoading';
import jsonRPC from './components/jsonRPC';
import getRequestId from './components/getRequestId';
import Message from './components/Message';

const theme = createMuiTheme({
    palette: {
        primary: {
            main: '#0054A6'
        },
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

    count_try = 0

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
        let child = this.state.child;
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

        if (!child.has_a_child) {
            clearTimeout(window.getChildTimeout);
            if(this.count_try > 20){
                return (
                            <div>
                                 <Message text={t("error_noRequestID")}/>
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
                        <div>
                            <Message text={t('successMessage', { preferred_name: this.state.success.preferred_name, context: this.state.success.gender === 'M' ? 'male':'female' })}/>
                        </div>
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
                                                                           country={child.country}
                                                                           age={child.age + ' ' + t('ageYears')}
                                                                           gender={child.gender === 'M' ? 'Male':'Female'}
                                                                           image_url={child.image_url}
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