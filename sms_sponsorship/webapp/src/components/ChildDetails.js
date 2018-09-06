import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import ListItem from '@material-ui/core/ListItem';
import ChildDescription from './ChildDescription';
import Collapse from '@material-ui/core/Collapse';
import ExpandLess from '@material-ui/icons/ExpandLess';
import ExpandMore from '@material-ui/icons/ExpandMore';
import Typography from '@material-ui/core/Typography';

const styles = {
    root: {
        width: '100%',
    },
};

class NestedList extends React.Component {
    state = { open: false };

    handleClick = () => {
        this.setState(state => ({ open: !state.open }));
    };

    render() {
        const { classes, t } = this.props;

        return (
            <div className={classes.root}>
                <ListItem button onClick={this.handleClick} style={{backgroundColor: '#0054A6', color: 'white', justifyContent: 'center'}}>
                    {/*<ListItemText primary="More details" />*/}
                    <Typography variant="button" style={{color: 'white'}}>{t('more')}</Typography>
                    {this.state.open ? <ExpandLess /> : <ExpandMore />}
                </ListItem>
                <Collapse in={this.state.open} timeout="auto" unmountOnExit>
                    <ChildDescription appContext={this.props.appContext}/>
                </Collapse>
            </div>
        );
    }
}

NestedList.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(NestedList);
