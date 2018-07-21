import React from 'react';
import TopAppBar from './components/TopAppBar';
import ChildCard from './components/ChildCard';
import CircularProgress from '@material-ui/core/CircularProgress';
import Typography from '@material-ui/core/Typography';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import CenteredLoading from './components/CenteredLoading';
import jsonRPC from './components/jsonRPC';
import getRequestId from './components/getRequestId';

const theme = createMuiTheme({
    palette: {
        primary: {
            main: '#0054A6'
        },
    },
});

window.pageLoaded = false;
window.getChildTimeout = false;

class Main extends React.Component {
    state = {
        child: false,
        partner: false,
        success: false,
    };

    getChild = () => {
        if (!getRequestId()) {
            return;
        }
        let url = "/sms_sponsorship_api";

        let data = {
            child_request_id: getRequestId()
        };

        jsonRPC(url, data, (res) => {
            let child = JSON.parse(res.responseText).result[0];
            let partner = (typeof(child.partner) === 'undefined') ? false:child.partner[0];
            this.setState({
                child: child,
                partner: partner,
            });
        });
    };

    componentDidMount() {
        if (!window.pageLoaded) {
            window.pageLoaded = true;
            this.getChild();
        }
    }

    render() {
        let child = this.state.child;
        let topAppBar = <TopAppBar title="Compassion"/>;

        if (!getRequestId()) {
            return (
                <div>
                    {topAppBar}
                    <div>
                        <CenteredLoading text="Error : no SMS request ID. Please send an other SMS."/>
                    </div>
                </div>
            )
        }

        if (!child.has_a_child) {
            clearTimeout(window.getChildTimeout);
            window.getChildTimeout = setTimeout(() => {
                this.getChild();
            }, 1000);
        }

        if (this.state.success) {
            return (
                <div>success !</div>
            )
        }

        return (
            <div>
                {topAppBar}
                {child ? (
                    <div>
                        {!child.invalid_sms_child_request ? (
                            <div>
                                {child.has_a_child ? (
                                    <ChildCard centered
                                               name={child.name}
                                               country={child.field_office_id[1]}
                                               age={child.age + ' years'}
                                               gender={child.gender === 'M' ? 'Male':'Female'}
                                               image_url={child.image_url}
                                               appContext={this}/>
                                ):(
                                    <CenteredLoading text="no child reserved, please wait a few seconds"/>
                                )}
                            </div>
                        ):(
                            <div>
                                <CenteredLoading text="Error : child request invalid"/>
                            </div>
                        )}
                    </div>
                ):(
                    <div>
                        <CenteredLoading text="loading..."/>
                    </div>
                )}
            </div>
        )
    }
}

export default () => {
    return (
        <MuiThemeProvider theme={theme}>
            <Main/>
        </MuiThemeProvider>
    );
}