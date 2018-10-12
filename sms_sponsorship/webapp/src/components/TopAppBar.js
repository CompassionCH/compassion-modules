import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import LogoWhite from '../images/LogoWhite.png';
import Button from '@material-ui/core/Button';
import LangDialog from "./LangDialog";
import Language from "@material-ui/icons/Language";
import IconButton from "@material-ui/core/IconButton/IconButton";

const styles = {
    root: {
        flexGrow: 1,
    },
    flex: {
        flexGrow: 1,
    },
    grow: {
        flexGrow: 1,
        textAlign: 'center',
    },
    menuButton: {
        marginLeft: -12,
        marginRight: 20,
    },
};


function ButtonAppBar(props) {
    const { classes, t } = props;
    return (
        <div className={classes.root}>
            <LangDialog appContext={props.appContext}
                        t={props.t}/>
            <AppBar position="static">
                <Toolbar>
                    <div className={classes.grow}>
                        <img src={LogoWhite} height="60px" alt={props.title} />
                    </div>
                    <IconButton color="inherit"
                                onClick={() => { props.appContext.setState({langDialog: true}) }}>
                        <Language />
                    </IconButton>
                    <Button
                        color="inherit"
                        onClick={() => { props.appContext.setState({langDialog: true}) }}
                    >
                        {t("langButton")}
                    </Button>
                </Toolbar>
            </AppBar>
        </div>
    );
}

ButtonAppBar.propTypes = {
    classes: PropTypes.object.isRequired,
};

export default withStyles(styles)(ButtonAppBar);