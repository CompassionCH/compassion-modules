import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import CardHeader from '@material-ui/core/CardHeader';
import Avatar from '@material-ui/core/Avatar';
import Typography from '@material-ui/core/Typography';
import SponsorForm from './SponsorForm';
import ChildDetails from './ChildDetails';
import classNames from 'classnames';


const styles = {
    card: {
        maxWidth: 450,
    },
    media: {
        height: 525,
        maxWidth: 400,
        marginLeft: 'auto',
        marginRight: 'auto'
    },
    centeredCard: {
        maxWidth: 1000,
        marginLeft: 'auto',
        marginRight: 'auto',
        paddingTop: 20
    },
    avatar: {
        margin: 'auto',
    },
    bigAvatar: {
        width: 150,
        height: 150,
    },
    headline: {
        display: 'flex',
        height: '100%',
        alignItems: 'center'
    },
    cardAction: {
        padding: '20px'
    }
};


function SimpleMediaCard(props) {
    const { classes, image_url, t } = props;
    const cardClass = !props.centered ? classes.card : classes.centeredCard;
    return (
        <div>
            <Card className={cardClass}>
                <CardHeader title={t("cardTitle")}/>
                <Avatar
                    alt={props.preferred_name}
                    src={image_url}
                    className={classNames(classes.avatar, classes.bigAvatar)}
                />
                <CardContent>
                    <Typography gutterBottom variant="title" align="center">
                        {props.name}
                    </Typography>
                    <Typography variant="subheading" align="center" style={{color: '#0054A6'}}>
                        {props.age}, {props.country}, {t(props.gender)}
                    </Typography>
                </CardContent>
                <CardActions className={classes.cardAction}>
                    <ChildDetails appContext={props.appContext} t={t}/>
                </CardActions>
                <CardContent>
                    <SponsorForm appContext={props.appContext} t={t}/>
                </CardContent>
            </Card>
        </div>
    );
}

SimpleMediaCard.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(SimpleMediaCard);
