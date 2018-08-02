import React from 'react';
import Typography from '@material-ui/core/Typography';
import CircularProgress from '@material-ui/core/CircularProgress';

export default class extends React.Component {
    render() {
        let styles = {
            loadingContainer: {
                display: 'table-cell',
                verticalAlign: 'middle',
                height: '80vh',
            },
            loadingTextContainer: {
                width: '80%',
                margin: 'auto',
                textAlign: 'center',
                paddingTop: 10,
            },
            circularProgressContainer: {
                marginLeft: '50%',
                position: 'relative',
                right: 15
            }
        };

        return (
           <div>
               <div style={styles.loadingContainer}>
                   <div style={styles.circularProgressContainer}>
                       <CircularProgress/>
                   </div>
                   <Typography component="p" style={styles.loadingTextContainer}>
                       {this.props.text}
                   </Typography>
               </div>
           </div>
        );
    }
}