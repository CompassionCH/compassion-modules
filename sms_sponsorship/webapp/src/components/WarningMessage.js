import React from 'react';

export default class extends React.Component {
    render() {
        let styles = {
            alert: {
                maxWidth: 960,
                marginTop: 15,
                marginLeft: "auto",
                marginRight: "auto",
                padding: 20,
                color: "#856404",
                backgroundColor: "#fff3cd",
                borderColor: "#ffeeba",
                borderStyle: "solid",
                borderWidth: 2,
                marginBottom: 15,
                borderRadius: 5
            },
        };

        return (
           <div style={styles.alert}>
               {this.props.text}
           </div>
        );
    }
}