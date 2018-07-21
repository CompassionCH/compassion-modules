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
        height: 0,
        paddingTop: '120%',
    },
    centeredCard: {
        maxWidth: 450,
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
                    image={props.image_url.replace('/w_150', '')}
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
                    <ChildDetails/>
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
