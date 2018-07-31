import React from 'react';
import PropTypes from 'prop-types';
import { withStyles } from '@material-ui/core/styles';
import SwipeableViews from 'react-swipeable-views';
import AppBar from '@material-ui/core/AppBar';
import Tabs from '@material-ui/core/Tabs';
import Tab from '@material-ui/core/Tab';
import Typography from '@material-ui/core/Typography';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';

function TabContainer({ children, dir }) {
    return (
        <Typography component="div" dir={dir} style={{ padding: 8 * 3 }}>
            {children}
        </Typography>
    );
}

TabContainer.propTypes = {
    children: PropTypes.node.isRequired,
    dir: PropTypes.string.isRequired,
};

const no_shadows = createMuiTheme({
    shadows: Array(25).fill('none')
});

const styles = theme => ({
    root: {
        backgroundColor: theme.palette.background.paper,
        width: '100%',
    },
    tab: {
        backgroundColor: 'white'
    },
    tabText: {
        marginTop: -5,
        marginLeft: -24,
        marginRight: -24,
        textAlign: 'justify'
    },
    container: {
        marginLeft: 10,
        marginRight: 10,
    },
    tabTitle: {
        marginBottom: 10
    }
});

class FullWidthTabs extends React.Component {
    handleChange = (event, value) => {
        this.props.sponsorFormContext.setState({ sp_plus_value: value });
    };

    handleChangeIndex = index => {
        this.props.sponsorFormContext.setState({ sp_plus_value: index });
    };

    render() {
        const { classes, theme } = this.props;

        return (
            <MuiThemeProvider theme={no_shadows}>
                <div className={classes.container}>
                    <div className={classes.root}>
                        <AppBar position="static" color="default">
                            <Tabs centered
                                value={this.props.sponsorFormContext.state.sp_plus_value}
                                onChange={this.handleChange}
                                indicatorColor="primary"
                                textColor="primary"
                                fullWidth
                            >
                                <Tab className={classes.tab} label="Sponsorship basic" />
                                <Tab className={classes.tab} label="Sponsorship plus" />
                            </Tabs>
                        </AppBar>
                        <SwipeableViews
                            axis={theme.direction === 'rtl' ? 'x-reverse' : 'x'}
                            index={this.props.sponsorFormContext.state.sp_plus_value}
                            onChangeIndex={this.handleChangeIndex}
                        >
                            <TabContainer dir={theme.direction}>
                                <div className={classes.tabText}>
                                    <div className={classes.tabTitle}>
                                        <Typography variant="title" align="center">CHF 42.-</Typography>
                                    </div>
                                </div>
                            </TabContainer>
                            <TabContainer dir={theme.direction}>
                                <div className={classes.tabText}>
                                    <div className={classes.tabTitle}>
                                        <Typography variant="title" align="center">CHF 50.-</Typography>
                                    </div>
                                    Sponsorship Plus is the basic sponsorship (CHF 42.-)
                                    plus an additional donation of CHF 8.00 per month: it enables Compassion to finance
                                    projects to change the children's environment.
                                    The funds received under the Sponsorship Plus program contribute to a common fund
                                    and enable Compassion to support several projects each year.
                                </div>
                            </TabContainer>
                        </SwipeableViews>
                    </div>
                </div>
            </MuiThemeProvider>
        );
    }
}

FullWidthTabs.propTypes = {
    classes: PropTypes.object.isRequired,
    theme: PropTypes.object.isRequired,
};

export default withStyles(styles, { withTheme: true })(FullWidthTabs);
