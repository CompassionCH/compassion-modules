import React from 'react';
import PropTypes from 'prop-types';
import classNames from "classnames";
import Avatar from "@material-ui/core/Avatar";
import Typography from '@material-ui/core/Typography';
import {withStyles} from "@material-ui/core/styles";
import CardHeader from "@material-ui/core/CardHeader/CardHeader";

const styles = {
    avatar: {
        margin: 'auto',
    },
    bigAvatar: {
        width: 150,
        height: 150,
    },
    loadingContainer: {
        verticalAlign: 'middle',
        marginTop: '20px',
        textAlign: 'center',
    },
    loadingTextContainer: {
        width: '80%',
        textAlign: 'center',
        margin: 'auto'
    },
};


function SuccessMessage(props)  {
    const {classes, preferred_name, t, image_url} = props;

    return (
        <div className={classes.loadingContainer}>
            <CardHeader title={t('successTitle', {preferred_name: preferred_name})}/>
            <Avatar
                alt={preferred_name}
                src={image_url}
                className={classNames(classes.avatar, classes.bigAvatar)}
            />
            <div className={classes.loadingTextContainer}>
                <Typography style={{marginTop: '20px'}}>
                    {t('successMessage1', { preferred_name: preferred_name})}
                </Typography>
                <br/>
                <Typography>
                    {t('successMessage2', { preferred_name: preferred_name})}
                </Typography>
            </div>
        </div>
    )
}

SuccessMessage.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(SuccessMessage);
