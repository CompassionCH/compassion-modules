import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import Card from '@material-ui/core/Card';
import CardActions from '@material-ui/core/CardActions';
import CardContent from '@material-ui/core/CardContent';
import CardMedia from '@material-ui/core/CardMedia';
import Button from '@material-ui/core/Button';
import Typography from '@material-ui/core/Typography';
import SponsorForm from './SponsorForm';
import ChildDetails from './ChildDetails';


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
        marginRight: 'auto'
    },
};

function SimpleMediaCard(props) {
    const { classes } = props;
    const cardClass = !props.centered ? classes.card : classes.centeredCard;
    return (
        <div>
            <Card className={cardClass}>
                <CardMedia
                    className={classes.media}
                    image={props.image_url.replace('/w_150', '')
                        .replace('media.ci.org/', 'media.ci.org/g_face,c_thumb,w_400,h_525,z_0.6/')}
                />
                <CardContent>
                    <Typography gutterBottom variant="headline" component="h2">
                        {props.name}
                    </Typography>
                    <Typography component="p">
                        Country : {props.country}
                    </Typography>
                    <Typography component="p">
                        Age : {props.age}
                    </Typography>
                    <Typography component="p">
                        Gender : {props.gender}
                    </Typography>
                </CardContent>
                <CardActions>
                    <ChildDetails appContext={props.appContext}/>
                </CardActions>
                <CardContent>
                    <SponsorForm appContext={props.appContext}/>
                </CardContent>
            </Card>
        </div>
    );
}

SimpleMediaCard.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(SimpleMediaCard);
