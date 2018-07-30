import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';
import Typography from '@material-ui/core/Typography';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import FormControl from '@material-ui/core/FormControl';
import FormHelperText from '@material-ui/core/FormHelperText';
import Switch from '@material-ui/core/Switch';
import SponsorshipPlusTabs from './SponsorshipPlusTabs';
import Button from '@material-ui/core/Button';
import ModalForm from './ModalForm';
import getRequestId from "./getRequestId";
import jsonRPC from "./jsonRPC";
import i18n from '../i18n';

const styles = theme => ({
    container: {
        display: 'flex',
        flexWrap: 'wrap',
    },
    textField: {
        marginLeft: theme.spacing.unit,
        marginRight: theme.spacing.unit,
        width: '100%',
    },
    sponsorButton: {
        marginRight: 7,
        marginBottom: 20,
        float: 'right',
    },
    sponsorPlusTabs: {
        marginTop: 15
    }
});

class TextFields extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            sp_plus_value: 1,
            partner: props.appContext.state.partner,
            dialogOpen: false
        };

        if (!this.state.partner) {
            this.state.partner = {
                firstname: '',
                lastname: '',
                email: ''
            }
        }
    }

    handleChange = name => event => {
        let initialPartner = {
            ...this.state.partner
        };
        initialPartner[name] = event.target.value;
        this.setState({
            partner: {
                ...initialPartner
            }
        });
    };

    sponsorFormHandler = () => {
        let requestId = getRequestId();
        let url = "/sms_sponsorship/step1/" + requestId + "/confirm";
        let lang = i18n.languages[1];
        let sponsor_form = document.forms.sponsor_form;
        let data = {
            firstname: sponsor_form.firstname.value,
            lastname: sponsor_form.lastname.value,
            email: sponsor_form.email.value,
            sponsorship_plus: sponsor_form.sponsorship_plus.checked,
            lang: lang,
        };
        const { preferred_name, gender} = this.props.appContext.state.child;
        this.props.appContext.setState({child: false});
        jsonRPC(url, data, (res) => {
            if (JSON.parse(res.responseText).result.result === 'success') {
                this.props.appContext.setState({success: {preferred_name: preferred_name, gender: gender}});
            }
        });
    };

    render() {
        const { classes, t } = this.props;

        let partner = this.state.partner;

        return (
            <div>
                <Typography variant="title">
                    {t("coordinates")}
                </Typography>
                <form id="sponsor_form" className={classes.container} noValidate autoComplete="off">
                    <TextField
                        id="firstname"
                        label={t("firstname")}
                        className={classes.textField}
                        onChange={this.handleChange('firstname')}
                        value={partner.firstname}
                        margin="dense"
                    />
                    <TextField
                        id="lastname"
                        label={t("lastname")}
                        className={classes.textField}
                        onChange={this.handleChange('lastname')}
                        value={partner.lastname}
                        margin="dense"
                    />
                    <TextField
                        id="email"
                        label={t("email")}
                        onChange={this.handleChange('email')}
                        type="email"
                        className={classes.textField}
                        value={partner.email}
                        margin="dense"
                    />
                    {/*invisible checkbox for sponsorship plus*/}
                    <input readOnly
                           type="checkbox"
                           id="sponsorship_plus"
                           style={{display: 'none'}}
                           checked={this.state.sp_plus_value === 1}/>
                    <div className={classes.sponsorPlusTabs}>
                        <SponsorshipPlusTabs sponsorFormContext={this}/>
                    </div>
                </form>
                <ModalForm sponsorFormContext={this}
                           appContext={this.props.appContext}
                           t={t}/>
                <Button variant="contained"
                        onClick={() => { this.setState({dialogOpen: true}) }}
                        color="primary">
                    {t('otherChild')}
                </Button>
                <Button className={classes.sponsorButton}
                        variant="contained"
                        onClick={this.sponsorFormHandler}
                        color="primary">
                    {t("sponsorNow")}
                </Button>
            </div>
        );
    }
}

TextFields.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(TextFields);
