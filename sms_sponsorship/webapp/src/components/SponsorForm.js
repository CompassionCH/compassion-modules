import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import TextField from '@material-ui/core/TextField';
import Typography from '@material-ui/core/Typography';
import FormControlLabel from '@material-ui/core/FormControlLabel';
import Switch from '@material-ui/core/Switch';
import Button from '@material-ui/core/Button';
import ModalForm from './ModalForm';
import getRequestId from "./getRequestId";
import jsonRPC from "./jsonRPC";

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
    }
});

class TextFields extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            sp_plus: true,
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
        let url = '/sms_sponsor_confirm';
        let sponsor_form = document.forms.sponsor_form;
        let data = {
            firstname: sponsor_form.firstname.value,
            lastname: sponsor_form.lastname.value,
            email: sponsor_form.email.value,
            sponsorship_plus: sponsor_form.sponsorship_plus.checked,
            child_request_id: getRequestId()
        };
        this.props.appContext.setState({child: false});
        jsonRPC(url, data, (res) => {
            if (JSON.parse(res.responseText).result.result === 'success') {
                this.props.appContext.setState({success: true});
            }
        });
    };

    render() {
        const { classes } = this.props;

        let partner = this.state.partner;

        return (
            <div>
                <Typography variant="title">
                    Your coordinates
                </Typography>
                <form id="sponsor_form" className={classes.container} noValidate autoComplete="off">
                    <TextField
                        id="firstname"
                        label="Firstname"
                        className={classes.textField}
                        onChange={this.handleChange('firstname')}
                        value={partner.firstname}
                        margin="dense"
                    />
                    <TextField
                        id="lastname"
                        label="Lastname"
                        className={classes.textField}
                        onChange={this.handleChange('lastname')}
                        value={partner.lastname}
                        margin="dense"
                    />
                    <TextField
                        id="email"
                        label="Email"
                        onChange={this.handleChange('email')}
                        type="email"
                        className={classes.textField}
                        value={partner.email}
                        margin="dense"
                    />
                    <FormControlLabel
                        style={{marginLeft: -5, marginTop: 8}}
                        control={
                            <Switch
                                id="sponsorship_plus"
                                className={classes.compassionSwitch}
                                checked={this.state.sp_plus}
                                onChange={() => { this.setState({sp_plus: !this.state.sp_plus}) }}
                                color="primary"
                            />
                        }
                        label="Sponsorship plus"
                    />
                </form>
                <ModalForm sponsorFormContext={this} appContext={this.props.appContext}/>
                <Button variant="contained"
                        onClick={() => { this.setState({dialogOpen: true}) }}
                        color="primary">
                    Other child
                </Button>
                <Button className={classes.sponsorButton}
                        variant="contained"
                        onClick={this.sponsorFormHandler}
                        color="primary">
                    Sponsor now
                </Button>
            </div>
        );
    }
}

TextFields.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(TextFields);
