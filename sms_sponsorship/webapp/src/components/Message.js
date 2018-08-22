import React from 'react';

export default class extends React.Component {
    render() {
        let styles = {
            loadingContainer: {
                verticalAlign: 'middle',
                marginTop: '120px',
                marginBottom: '50px',
                textAlign: 'center'
            },
            loadingTextContainer: {
                width: '80%',
                textAlign: 'center',
                margin: 'auto'
            },
        };

        return (
            <div style={styles.loadingContainer}>
                <div style={styles.loadingTextContainer} dangerouslySetInnerHTML={{__html: this.props.text}}/>
            </div>
        )
    }
}