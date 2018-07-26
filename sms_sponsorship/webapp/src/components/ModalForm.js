import React from 'react';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogContentText from '@material-ui/core/DialogContentText';
import DialogTitle from '@material-ui/core/DialogTitle';
import SelectForm from './SelectForm';

export default class FormDialog extends React.Component {
    handleClose = () => {
        this.props.sponsorFormContext.setState({ dialogOpen: false });
    };

    render() {
        let countries = this.props.appContext.state.child.countries;

        let genders = [
            {value: 'Male', text:'Boy'},
            {value: 'Female', text:'Girl'}
        ];

        let age_slots = [
            {value:'0-3', text:'0-3 years'},
            {value:'4-6', text:'4-6 years'},
            {value:'7-10', text:'7-10 years'},
            {value:'11-14', text:'11-14 years'},
            {value:'15-20', text:'15-20 years'}
        ];

        return (
            <div>
                <Dialog
                    open={this.props.sponsorFormContext.state.dialogOpen}
                    onClose={this.handleClose}
                    aria-labelledby="form-dialog-title">
                    <DialogTitle id="form-dialog-title">Choose other child</DialogTitle>
                    <DialogContent>
                        <form id="other_child_form" autoComplete="off">
                            <DialogContentText>
                                Please select filters for an other child.<br/>
                                When nothing is selected, the filter doesn't apply.
                            </DialogContentText>
                            <SelectForm elements={genders} name="gender" text="Choose a boy or a girl"/>
                            <SelectForm elements={age_slots} name="age" text="Select age"/>
                            <SelectForm elements={countries} name="country" text="Choose a country"/>
                        </form>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={this.handleClose} color="default">
                            Cancel
                        </Button>
                        <Button onClick={this.props.appContext.changeChild} color="primary">
                            Choose other child
                        </Button>
                    </DialogActions>
                </Dialog>
            </div>
        );
    }
}
