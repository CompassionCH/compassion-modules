import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';
import Typography from '@material-ui/core/Typography';
import SponsorshipPlusTabs from './SponsorshipPlusTabs';
import Button from '@material-ui/core/Button';
import ModalForm from './ModalForm';
import getRequestId from "./getRequestId";
import jsonRPC from "./jsonRPC";
import i18n from '../i18n';
import Snackbar from "@material-ui/core/Snackbar/Snackbar";
import IconButton from "@material-ui/core/IconButton/IconButton";
import CloseIcon from '@material-ui/icons/Close';
import SnackbarContent from "@material-ui/core/SnackbarContent/SnackbarContent";
import ErrorIcon from '@material-ui/icons/Error';
import classNames from 'classnames';

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
    },
    icon: {
        fontSize: 20,
    },
    iconVariant: {
        opacity: 0.9,
        marginRight: theme.spacing.unit,
    },
    message: {
        display: 'flex',
        alignItems: 'center',
    },
});


class TextFields extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            sp_plus_value: 1,
            partner: props.appContext.state.partner,
            snackBarOpen: false,
            formErrors: false,
            message: ''
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

    handleCloseSnackbar = (event, reason) => {
        if (reason === 'clickaway') {
            return;
        }
        this.setState({ snackBarOpen: false });
    };

    sponsorFormHandler = () => {
        let requestId = getRequestId();
        let url = "/sms_sponsorship/step1/" + requestId + "/confirm";
        let lang = i18n.language;
        let sponsor_form = document.forms.sponsor_form;

        // Validate name
        if (! sponsor_form.firstname.value) {
            this.setState({
                snackBarOpen: true,
                message: this.props.t("error_missingFirstname"),
                formErrors: 'firstname'
            });
            return;
        }
        if (! sponsor_form.lastname.value) {
            this.setState({
                snackBarOpen: true,
                message: this.props.t("error_missingLastname"),
                formErrors: 'lastname'
            });
            return;
        }
        // Validate email field
        let email = sponsor_form.email.value;
        if (email !== sponsor_form.email2.value || email.indexOf('@') < 0) {
            this.setState({
                snackBarOpen: true,
                message: this.props.t("error_invalidMail"),
                formErrors: 'email'
            });
            return;
        }

        let data = {
            firstname: sponsor_form.firstname.value,
            lastname: sponsor_form.lastname.value,
            email: email,
            sponsorship_plus: sponsor_form.sponsorship_plus.checked,
            lang: lang,
        };
        const {preferred_name, image_url} = this.props.appContext.state.child;
        this.props.appContext.setState({child: false});
        jsonRPC(url, data, (res) => {
            if (JSON.parse(res.responseText).result.result === 'success') {
                this.props.appContext.setState({success: {preferred_name: preferred_name, image_url: image_url}});
            }
        });
    };

    render() {
        const { classes, t } = this.props;

        let partner = this.state.partner;

        return (
            <div>
                <Typography variant="title" style={{color: '#555555', marginLeft: '8px'}}>
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
                        required={true}
                        error={this.state.formErrors === 'firstname'}
                    />
                    <TextField
                        id="lastname"
                        label={t("lastname")}
                        className={classes.textField}
                        onChange={this.handleChange('lastname')}
                        value={partner.lastname}
                        margin="dense"
                        required={true}
                        error={this.state.formErrors === 'lastname'}
                    />
                    <TextField
                        id="email"
                        label={t("email")}
                        onChange={this.handleChange('email')}
                        type="email"
                        className={classes.textField}
                        value={partner.email}
                        margin="dense"
                        required={true}
                        error={this.state.formErrors === 'email'}
                    />
                    <TextField
                        id="email2"
                        label={t("emailConfirm")}
                        type="email"
                        className={classes.textField}
                        margin="dense"
                        required={true}
                        error={this.state.formErrors === 'email'}
                    />
                    {/*invisible checkbox for sponsorship plus*/}
                    <input readOnly
                           type="checkbox"
                           id="sponsorship_plus"
                           style={{display: 'none'}}
                           checked={this.state.sp_plus_value === 1}/>
                    <div className={classes.sponsorPlusTabs}>
                        <SponsorshipPlusTabs sponsorFormContext={this} t={t}/>
                    </div>
                </form>
                <ModalForm sponsorFormContext={this}
                           appContext={this.props.appContext}
                           t={t}/>

                <div style={{textAlign: 'center'}}>
                    <Button variant="contained"
                            onClick={this.sponsorFormHandler}
                            color="primary"
                            fullWidth
                            size="medium"
                    >
                        {t("sponsorNow", {name: this.props.appContext.state.child.preferred_name})}
                    </Button>
                </div>
                <Snackbar
                    anchorOrigin={{
                        vertical: 'top',
                        horizontal: 'center',
                    }}
                    open={this.state.snackBarOpen}
                    autoHideDuration={6000}
                    onClose={this.handleCloseSnackbar}
                    ContentProps={{
                        'aria-describedby': 'message-id',
                    }}
                >
                    <SnackbarContent
                        aria-describedby="client-snackbar"
                        message={
                            <span id="client-snackbar" className={classes.message}>
                              <ErrorIcon className={classNames(classes.icon, classes.iconVariant)} />
                                            {this.state.message}
                            </span>
                        }
                        action={[
                            <IconButton
                                key="close"
                                aria-label="Close"
                                color="inherit"
                                className={classes.close}
                                onClick={this.handleCloseSnackbar}
                            >
                                <CloseIcon className={classes.icon} />
                            </IconButton>,
                        ]}
                    />
                </Snackbar>
            </div>
        );
    }
}

TextFields.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(TextFields);
