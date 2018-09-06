import React from 'react';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import SelectForm from './SelectForm';

export default class FormDialog extends React.Component {
    handleClose = () => {
        this.props.appContext.setState({ dialogOpen: false });
    };

    render() {
        const {t} = this.props;
        let countries = this.props.appContext.state.child.countries;

        let genders = [
            {value: 'Male', text:t('boy')},
            {value: 'Female', text:t('girl')}
        ];

        let age_slots = [
            {value:'0-3', text:t('ageCat1')},
            {value:'4-6', text:t('ageCat2')},
            {value:'7-10', text:t('ageCat3')},
            {value:'11-14', text:t('ageCat4')},
            {value:'15-20', text:t('ageCat5')}
        ];

        return (
            <div>
                <Dialog
                    open={this.props.appContext.state.dialogOpen}
                    onClose={this.handleClose}
                    aria-labelledby="form-dialog-title">
                    <DialogTitle id="form-dialog-title">{t('chooseTitle')}</DialogTitle>
                    <DialogContent>
                        <form id="other_child_form" autoComplete="off">
                            <DialogContentText>
                                {t('modalHelp')}
                            </DialogContentText>
                            <SelectForm elements={genders} name="gender" text={t("genderSelect")}/>
                            <SelectForm elements={age_slots} name="age" text={t("ageSelect")}/>
                            <SelectForm elements={countries} name="country" text={t("countrySelect")}/>
                        </form>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={this.handleClose} color="default">
                            {t("cancel")}
                        </Button>
                        <Button onClick={this.props.appContext.changeChild} color="primary">
                            {t('chooseTitle')}
                        </Button>
                    </DialogActions>
                </Dialog>
            </div>
        );
    }
}
