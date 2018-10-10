import React from 'react';
import Button from '@material-ui/core/Button';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';
import SelectForm from './SelectForm';

export default class LangDialog extends React.Component {
    handleClose = () => {
        this.props.appContext.setState({ langDialog: false });
    };

    render() {
        const {t} = this.props;

        let langs = [
            {value: 'fr', text:t('langFr')},
            {value: 'de', text:t('langDe')},
            {value: 'en', text:t('langEn')},
            {value: 'it', text:t('langIt')},
        ];

        return (
            <div>
                <Dialog
                    open={this.props.appContext.state.langDialog}
                    onClose={this.handleClose}
                    aria-labelledby="form-dialog-title">
                    <DialogTitle id="form-dialog-title">{t('langTitle')}</DialogTitle>
                    <DialogContent>
                        <form id="lang_form">
                            <SelectForm elements={langs} name="lang" text={t("langTitle")}/>
                        </form>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={this.handleClose} color="default">
                            {t("cancel")}
                        </Button>
                        <Button onClick={this.props.appContext.changeLanguage} color="primary">
                            {t('langAction')}
                        </Button>
                    </DialogActions>
                </Dialog>
            </div>
        );
    }
}
